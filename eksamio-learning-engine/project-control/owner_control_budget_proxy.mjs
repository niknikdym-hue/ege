#!/usr/bin/env node
import http from 'node:http';
import {Readable} from 'node:stream';

const PRICES = {
  'gpt-6-astra': {input: 10.0, output: 50.0},
  'gpt-5.6-sol': {input: 4.0, output: 20.0},
  'gpt-5.6-terra': {input: 2.0, output: 12.0},
  'gpt-5.6-luna': {input: 0.2, output: 1.2},
};

export function conservativeReservationUsd({model, payloadBytes, maxOutputTokens}) {
  const price = PRICES[model];
  if (!price) throw new Error(`unsupported model: ${model}`);
  // Safe upper bound: token count cannot exceed UTF-8 byte count. Price input at
  // cache-write rate (1.25x uncached) rather than assuming discounts.
  let inputRate = price.input * 1.25;
  let outputRate = price.output;
  if (payloadBytes > 272000) {
    inputRate *= 2.0;
    outputRate *= 1.5;
  }
  return (payloadBytes * inputRate + maxOutputTokens * outputRate) / 1_000_000;
}

export function capOutputTokens({model, payloadBytes, requested, remainingUsd, routeCap = 2400}) {
  const price = PRICES[model];
  if (!price) throw new Error(`unsupported model: ${model}`);
  let inputRate = price.input * 1.25;
  let outputRate = price.output;
  if (payloadBytes > 272000) {
    inputRate *= 2.0;
    outputRate *= 1.5;
  }
  const inputCost = payloadBytes * inputRate / 1_000_000;
  const room = remainingUsd - inputCost;
  if (room <= 0) return 0;
  const byBudget = Math.floor(room * 1_000_000 / outputRate);
  return Math.max(0, Math.min(Number(requested || routeCap), routeCap, byBudget));
}

function selfTest() {
  const c1 = conservativeReservationUsd({model:'gpt-5.6-terra', payloadBytes:100000, maxOutputTokens:2000});
  if (!(c1 > 0.14 && c1 < 0.16)) throw new Error(`unexpected Terra reservation ${c1}`);
  const capped = capOutputTokens({model:'gpt-6-astra', payloadBytes:100000, requested:12000, remainingUsd:1.5, routeCap:4000});
  if (!(capped > 0 && capped <= 4000)) throw new Error(`unexpected Astra cap ${capped}`);
  const blocked = capOutputTokens({model:'gpt-6-astra', payloadBytes:200000, requested:12000, remainingUsd:0.1, routeCap:4000});
  if (blocked !== 0) throw new Error(`expected blocked request, got ${blocked}`);
  console.log('OWNER_CONTROL_BUDGET_PROXY_SELFTEST=PASS');
}

if (process.argv.includes('--self-test')) {
  selfTest();
  process.exit(0);
}

const listenPort = Number(process.env.OWNER_BUDGET_PROXY_PORT || 8787);
const totalBudget = Number(process.env.OWNER_TASK_BUDGET_USD || '0');
const allowedModels = new Set((process.env.OWNER_ALLOWED_MODELS || '').split(',').map(x => x.trim()).filter(Boolean));
if (!(totalBudget > 0 && totalBudget <= 10)) throw new Error('OWNER_TASK_BUDGET_USD must be >0 and <=10');
if (!allowedModels.size) throw new Error('OWNER_ALLOWED_MODELS is required');

let apiKey = '';
for await (const chunk of process.stdin) apiKey += chunk.toString('utf8');
apiKey = apiKey.trim();
if (!apiKey) throw new Error('OpenAI API key was not supplied on stdin');
let remainingUsd = totalBudget;
let reservedUsd = 0;
let requestCount = 0;

const routeCaps = {
  'gpt-5.6-luna': 1800,
  'gpt-5.6-terra': 2200,
  'gpt-5.6-sol': 2400,
  'gpt-6-astra': 3000,
};

function jsonError(res, status, message) {
  const body = JSON.stringify({error:{message,type:'owner_control_budget_guard'}});
  res.writeHead(status, {'content-type':'application/json','content-length':Buffer.byteLength(body)});
  res.end(body);
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'GET' && req.url === '/health') {
    const body = JSON.stringify({status:'ok', remaining_usd:Number(remainingUsd.toFixed(6)), reserved_usd:Number(reservedUsd.toFixed(6)), requests:requestCount});
    res.writeHead(200, {'content-type':'application/json'}); res.end(body); return;
  }
  if (req.method !== 'POST' || !req.url?.endsWith('/v1/responses')) {
    jsonError(res, 404, 'only POST /v1/responses is allowed'); return;
  }
  try {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const raw = Buffer.concat(chunks);
    let payload;
    try { payload = JSON.parse(raw.toString('utf8')); }
    catch { jsonError(res, 400, 'invalid JSON'); return; }
    const model = String(payload.model || '');
    if (!allowedModels.has(model) || !PRICES[model]) {
      jsonError(res, 403, `model ${model || '<empty>'} is not allowed for this task`); return;
    }
    // Full serialized request bytes are intentionally used as a conservative
    // input-token upper bound; this over-reserves rather than overspends.
    const provisional = Buffer.byteLength(JSON.stringify(payload), 'utf8');
    const maxOut = capOutputTokens({
      model,
      payloadBytes: provisional,
      requested: payload.max_output_tokens,
      remainingUsd,
      routeCap: routeCaps[model],
    });
    if (maxOut < 256) {
      jsonError(res, 402, `hard task budget exhausted before provider call; remaining=$${remainingUsd.toFixed(4)}`); return;
    }
    payload.max_output_tokens = maxOut;
    payload.store = false;
    const encoded = Buffer.from(JSON.stringify(payload), 'utf8');
    const reservation = conservativeReservationUsd({model, payloadBytes:encoded.length, maxOutputTokens:maxOut});
    if (reservation > remainingUsd + 1e-9) {
      jsonError(res, 402, 'hard task budget reservation refused'); return;
    }
    remainingUsd -= reservation;
    reservedUsd += reservation;
    requestCount += 1;
    console.log(`OWNER_BUDGET_RESERVE request=${requestCount} model=${model} reserve=${reservation.toFixed(6)} remaining=${remainingUsd.toFixed(6)} max_output_tokens=${maxOut}`);

    const upstream = await fetch('https://api.openai.com/v1/responses', {
      method:'POST',
      headers:{'authorization':`Bearer ${apiKey}`,'content-type':'application/json'},
      body:encoded,
    });
    const headers = {};
    for (const [k,v] of upstream.headers.entries()) {
      if (!['content-length','transfer-encoding','connection'].includes(k.toLowerCase())) headers[k] = v;
    }
    res.writeHead(upstream.status, headers);
    if (upstream.body) Readable.fromWeb(upstream.body).pipe(res); else res.end();
  } catch (error) {
    console.error(error);
    if (!res.headersSent) jsonError(res, 502, String(error?.message || error)); else res.end();
  }
});

server.listen(listenPort, '127.0.0.1', () => {
  console.log(`OWNER_CONTROL_BUDGET_PROXY_READY port=${listenPort} budget=${totalBudget.toFixed(4)} allowed=${[...allowedModels].join(',')}`);
});

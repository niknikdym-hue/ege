(function(root,factory){
"use strict";
var api=factory();
if(typeof module!=="undefined"&&module.exports)module.exports=api;
if(root)root.EksamioPEISBrowserHook=api;
})(typeof window!=="undefined"?window:null,function(){
"use strict";

var DIRECTIVE_FIELDS=[
  "recommendation_id",
  "action_type",
  "semantic_targets",
  "prerequisite_targets",
  "reason_codes",
  "verification_required",
  "learner_state_watermark",
  "route",
  "canonical_state_owner"
];

function cloneJson(value){
  if(value===undefined)return null;
  return JSON.parse(JSON.stringify(value));
}

function stableHash(text){
  var h=2166136261;
  for(var i=0;i<text.length;i++){
    h^=text.charCodeAt(i);
    h=Math.imul(h,16777619);
  }
  return("00000000"+(h>>>0).toString(16)).slice(-8);
}

function sanitizeDirective(response){
  if(!response||typeof response!=="object")return null;
  var source=response.directive;
  if(!source||typeof source!=="object")return null;
  if(source.canonical_state_owner!=="shared_peis")return null;
  var out={};
  DIRECTIVE_FIELDS.forEach(function(key){
    if(Object.prototype.hasOwnProperty.call(source,key))out[key]=cloneJson(source[key]);
  });
  return out;
}

function nonFatalCallback(callback,payload){
  if(typeof callback!=="function")return"NOT_CONFIGURED";
  try{
    callback(payload);
    return"DELIVERED";
  }catch(e){
    return"FAILED_OPEN";
  }
}

function settleWithTimeout(operation,timeoutMs){
  return new Promise(function(resolve){
    var settled=false;
    var timer=setTimeout(function(){
      if(settled)return;
      settled=true;
      resolve({kind:"TIMEOUT"});
    },timeoutMs);
    Promise.resolve().then(operation).then(function(value){
      if(settled)return;
      settled=true;
      clearTimeout(timer);
      resolve({kind:"VALUE",value:value});
    },function(error){
      if(settled)return;
      settled=true;
      clearTimeout(timer);
      resolve({kind:"ERROR",error:error});
    });
  });
}

function createBrowserHook(options){
  options=options||{};
  var enabled=options.enabled===true;
  var adapterId=typeof options.adapterId==="string"?options.adapterId:"";
  var transport=typeof options.transport==="function"?options.transport:null;
  var onDirective=typeof options.onDirective==="function"?options.onDirective:null;
  var onDiagnostic=typeof options.onDiagnostic==="function"?options.onDiagnostic:null;
  var clock=typeof options.clock==="function"?options.clock:function(){return new Date().toISOString();};
  var timeoutMs=Number(options.timeoutMs);
  if(!Number.isFinite(timeoutMs)||timeoutMs<1)timeoutMs=1500;
  if(timeoutMs>10000)timeoutMs=10000;

  function buildCheckedCardRequest(card,session){
    if(!card||typeof card.id!=="string"||!card.id)throw new Error("card.id is required");
    if(!session||!Number.isFinite(Number(session.startedAt))||Number(session.startedAt)<=0)throw new Error("session.startedAt is required");
    if(session.mode!=="practice"&&session.mode!=="exam")throw new Error("session.mode is invalid");
    if(!session.answers||!Object.prototype.hasOwnProperty.call(session.answers,card.id))throw new Error("session answer is missing");
    if(!adapterId)throw new Error("adapterId is required");
    var requestKey=adapterId+"|"+String(session.startedAt)+"|"+card.id;
    return{
      adapter_id:adapterId,
      payload:{
        card_id:card.id,
        session_started_at_ms:Number(session.startedAt),
        session_mode:session.mode,
        answer:cloneJson(session.answers[card.id]),
        occurred_at_client:String(clock()),
        client_request_id:"bh."+stableHash(requestKey)
      }
    };
  }

  function observeCheckedCard(card,session){
    if(!enabled)return Promise.resolve({status:"DISABLED"});
    if(!transport)return Promise.resolve({status:"FAILED_OPEN",reason:"TRANSPORT_NOT_CONFIGURED"});
    var request;
    try{
      request=buildCheckedCardRequest(card,session);
    }catch(error){
      nonFatalCallback(onDiagnostic,{kind:"BUILD_FAILED",message:String(error&&error.message||error)});
      return Promise.resolve({status:"FAILED_OPEN",reason:"BUILD_FAILED"});
    }
    return settleWithTimeout(function(){return transport(cloneJson(request));},timeoutMs).then(function(result){
      if(result.kind==="TIMEOUT"){
        nonFatalCallback(onDiagnostic,{kind:"TRANSPORT_TIMEOUT"});
        return{status:"FAILED_OPEN",reason:"TRANSPORT_TIMEOUT",request:request};
      }
      if(result.kind==="ERROR"){
        nonFatalCallback(onDiagnostic,{kind:"TRANSPORT_ERROR",message:String(result.error&&result.error.message||result.error)});
        return{status:"FAILED_OPEN",reason:"TRANSPORT_ERROR",request:request};
      }
      var directive=sanitizeDirective(result.value);
      if(!directive){
        nonFatalCallback(onDiagnostic,{kind:"DIRECTIVE_REJECTED"});
        return{status:"FAILED_OPEN",reason:"DIRECTIVE_REJECTED",request:request};
      }
      var callbackStatus=nonFatalCallback(onDirective,cloneJson(directive));
      return{
        status:"DELIVERED",
        directive:directive,
        callback_status:callbackStatus,
        request:request
      };
    });
  }

  return{
    enabled:enabled,
    buildCheckedCardRequest:buildCheckedCardRequest,
    observeCheckedCard:observeCheckedCard
  };
}

return{
  createBrowserHook:createBrowserHook,
  sanitizeDirective:sanitizeDirective,
  directiveFields:DIRECTIVE_FIELDS.slice()
};
});

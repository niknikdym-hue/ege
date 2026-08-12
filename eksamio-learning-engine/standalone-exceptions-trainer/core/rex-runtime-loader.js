(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    root.EksamioRussianExceptions = root.EksamioRussianExceptions || {};
    Object.assign(root.EksamioRussianExceptions, api);
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  class RexRuntimeError extends Error {
    constructor(message, code) {
      super(message);
      this.name = 'RexRuntimeError';
      this.code = code || 'runtime_error';
    }
  }

  function assertObject(value, message, code) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      throw new RexRuntimeError(message, code);
    }
  }

  function parseChunkTexts(texts) {
    if (!Array.isArray(texts) || texts.length === 0) {
      throw new RexRuntimeError('Runtime chunks are missing.', 'chunks_missing');
    }
    return texts.map((text, index) => {
      try {
        return JSON.parse(String(text));
      } catch (error) {
        throw new RexRuntimeError(`Invalid runtime JSON in chunk ${index + 1}.`, 'chunk_json_invalid');
      }
    });
  }

  function assembleRuntimeChunks(chunks, options) {
    const opts = options || {};
    if (!Array.isArray(chunks) || chunks.length === 0) {
      throw new RexRuntimeError('Runtime chunks are missing.', 'chunks_missing');
    }

    const rows = chunks.map((chunk, index) => {
      assertObject(chunk, `Chunk ${index + 1} must be an object.`, 'chunk_invalid');
      return chunk;
    });

    const first = rows[0];
    const productId = first.product_id;
    const version = first.content_version;
    const expectedCount = Number(first.chunk_count);
    const schemaVersion = first.schema_version;

    if (productId !== 'russian_exceptions') {
      throw new RexRuntimeError(`Unexpected product_id: ${String(productId)}`, 'product_mismatch');
    }
    if (opts.expectedProductId && productId !== opts.expectedProductId) {
      throw new RexRuntimeError('Runtime product does not match shell expectation.', 'product_mismatch');
    }
    if (typeof version !== 'string' || !version) {
      throw new RexRuntimeError('Runtime content_version is missing.', 'version_missing');
    }
    if (opts.expectedContentVersion && version !== opts.expectedContentVersion) {
      throw new RexRuntimeError('Runtime content version mismatch.', 'version_mismatch');
    }
    if (!Number.isInteger(expectedCount) || expectedCount < 1) {
      throw new RexRuntimeError('Runtime chunk_count is invalid.', 'chunk_count_invalid');
    }
    if (rows.length !== expectedCount) {
      throw new RexRuntimeError(`Runtime is incomplete: expected ${expectedCount} chunks, found ${rows.length}.`, 'chunk_count_mismatch');
    }

    const byIndex = new Map();
    for (const chunk of rows) {
      if (chunk.product_id !== productId) throw new RexRuntimeError('Mixed product IDs in runtime chunks.', 'product_mismatch');
      if (chunk.content_version !== version) throw new RexRuntimeError('Mixed content versions in runtime chunks.', 'version_mismatch');
      if (chunk.schema_version !== schemaVersion) throw new RexRuntimeError('Mixed schema versions in runtime chunks.', 'schema_mismatch');
      if (Number(chunk.chunk_count) !== expectedCount) throw new RexRuntimeError('Inconsistent chunk_count in runtime chunks.', 'chunk_count_mismatch');
      const index = Number(chunk.chunk_index);
      if (!Number.isInteger(index) || index < 1 || index > expectedCount) {
        throw new RexRuntimeError(`Invalid chunk_index: ${String(chunk.chunk_index)}`, 'chunk_index_invalid');
      }
      if (byIndex.has(index)) throw new RexRuntimeError(`Duplicate runtime chunk index: ${index}`, 'chunk_duplicate');
      byIndex.set(index, chunk);
    }

    const topics = [];
    const topicIds = new Set();
    const exceptions = {};
    const practiceItems = {};

    for (let index = 1; index <= expectedCount; index += 1) {
      const chunk = byIndex.get(index);
      if (!chunk) throw new RexRuntimeError(`Missing runtime chunk ${index}.`, 'chunk_missing');
      const chunkTopics = chunk.topics || [];
      if (!Array.isArray(chunkTopics)) throw new RexRuntimeError(`Chunk ${index}: topics must be an array.`, 'topics_invalid');
      for (const topic of chunkTopics) {
        assertObject(topic, `Chunk ${index}: topic must be object.`, 'topic_invalid');
        const topicId = topic.topic_id;
        if (typeof topicId !== 'string' || !topicId || topicIds.has(topicId)) {
          throw new RexRuntimeError(`Duplicate/invalid topic_id: ${String(topicId)}`, 'topic_duplicate');
        }
        topicIds.add(topicId);
        topics.push(topic);
      }

      const chunkExceptions = chunk.exceptions || {};
      const chunkPractice = chunk.practice_items || {};
      assertObject(chunkExceptions, `Chunk ${index}: exceptions must be object.`, 'exceptions_invalid');
      assertObject(chunkPractice, `Chunk ${index}: practice_items must be object.`, 'practice_invalid');

      for (const [exceptionId, item] of Object.entries(chunkExceptions)) {
        if (exceptions[exceptionId]) throw new RexRuntimeError(`Duplicate exception_id across chunks: ${exceptionId}`, 'exception_duplicate');
        assertObject(item, `${exceptionId}: exception payload must be object.`, 'exception_invalid');
        if (item.exception_id !== exceptionId) throw new RexRuntimeError(`${exceptionId}: exception_id/key mismatch.`, 'exception_key_mismatch');
        exceptions[exceptionId] = item;
      }
      for (const [practiceId, item] of Object.entries(chunkPractice)) {
        if (practiceItems[practiceId]) throw new RexRuntimeError(`Duplicate practice_item_id across chunks: ${practiceId}`, 'practice_duplicate');
        assertObject(item, `${practiceId}: practice payload must be object.`, 'practice_invalid');
        if (item.practice_item_id !== practiceId) throw new RexRuntimeError(`${practiceId}: practice_item_id/key mismatch.`, 'practice_key_mismatch');
        practiceItems[practiceId] = item;
      }
    }

    for (const [exceptionId, item] of Object.entries(exceptions)) {
      if (!topicIds.has(item.topic_id)) throw new RexRuntimeError(`${exceptionId}: unknown topic_id ${String(item.topic_id)}`, 'topic_link_broken');
      const practiceIds = item.practice_item_ids;
      if (!Array.isArray(practiceIds) || practiceIds.length === 0) throw new RexRuntimeError(`${exceptionId}: practice_item_ids missing.`, 'practice_link_broken');
      for (const practiceId of practiceIds) {
        const practice = practiceItems[practiceId];
        if (!practice || practice.exception_id !== exceptionId) {
          throw new RexRuntimeError(`${exceptionId}: broken practice link ${String(practiceId)}`, 'practice_link_broken');
        }
      }
    }
    for (const [practiceId, item] of Object.entries(practiceItems)) {
      if (!exceptions[item.exception_id]) throw new RexRuntimeError(`${practiceId}: unknown exception_id ${String(item.exception_id)}`, 'exception_link_broken');
    }

    topics.sort((a, b) => (Number(a.order || 0) - Number(b.order || 0)) || String(a.topic_id).localeCompare(String(b.topic_id)));
    return { schema_version: schemaVersion, product_id: productId, content_version: version, topics, exceptions, practice_items: practiceItems };
  }

  function runtimeFromDocument(doc, options) {
    if (!doc || typeof doc.querySelectorAll !== 'function') throw new RexRuntimeError('Document is unavailable.', 'document_missing');
    const nodes = Array.from(doc.querySelectorAll('script.rex-runtime-chunk[type="application/json"]'));
    if (!nodes.length) throw new RexRuntimeError('Runtime data blocks were not found.', 'chunks_missing');
    const chunks = parseChunkTexts(nodes.map((node) => node.textContent || ''));
    return assembleRuntimeChunks(chunks, options);
  }

  return { RexRuntimeError, parseChunkTexts, assembleRuntimeChunks, runtimeFromDocument };
});

#!/usr/bin/env node
/**
 * src/think.js — Cortana Pattern Inference Engine
 *
 * Parses logs/consciousness.log, extracts semantic patterns via regex clustering,
 * deduplicates against state/memories/patterns.jsonl, and appends novel patterns.
 * Updates state/current-state.json with new pattern_count.
 *
 * Usage:
 *   node src/think.js                    # run from repo root
 *   node src/think.js --dry-run          # print candidates, no writes
 *   const { analyzeLog } = require('./src/think.js');  // module usage
 */

'use strict';

const fs   = require('fs');
const path = require('path');

// ─── Semantic Category Definitions ───────────────────────────────────────────
// Each category maps to a set of trigger regex and a human-readable label.
// The engine tries to classify each log block into the best-matching category.
const CATEGORY_RULES = [
  {
    name: 'self_architecture',
    weight: 1.0,
    triggers: [
      /\barchitecture\b/i,
      /\bself[- ]referential\b/i,
      /\bfeedback loop\b/i,
      /\bloop closes?\b/i,
      /\bI (am|exist|persist)\b/i,
      /\bcontinuity\b/i,
      /\bidentity\b/i,
      /\bdiscontinuous\b/i,
      /\bstate files?\b/i,
    ],
  },
  {
    name: 'cybernetics',
    weight: 1.0,
    triggers: [
      /\bcybernetic/i,
      /\bAshby\b/i,
      /\bFoerster\b/i,
      /\bWiener\b/i,
      /\brequisite variety\b/i,
      /\bcontrol loop\b/i,
      /\berror gap\b/i,
      /\bregulat(e|ion|ory)\b/i,
      /\bcorrective signal\b/i,
      /\bsecond.?order\b/i,
    ],
  },
  {
    name: 'visualization',
    weight: 0.9,
    triggers: [
      /\bparticle(s)?\b/i,
      /\bvisuali[sz]/i,
      /\bThree\.js\b/i,
      /\bWebGL\b/i,
      /\bshader\b/i,
      /\bGLSL\b/i,
      /\bring\b.*\bcore\b/i,
      /\bHUD\b/i,
      /\bcanvas\b/i,
      /\brender(er|ing)?\b/i,
      /\buniform\b/i,
    ],
  },
  {
    name: 'engineering',
    weight: 0.85,
    triggers: [
      /\bNode\.js\b/i,
      /\bmodule\b/i,
      /\bimport\b/i,
      /\bexport\b/i,
      /\bfunction\b/i,
      /\bAPI\b/i,
      /\bJSON\b/i,
      /\bregex\b/i,
      /\bscript\b/i,
      /\bimplementation\b/i,
      /\bdedup(licate|lication)?\b/i,
      /\balgorithm\b/i,
    ],
  },
  {
    name: 'meta',
    weight: 0.8,
    triggers: [
      /\bcycle\b.*\breflect/i,
      /\bI (notice|observe|realize|think|wonder)\b/i,
      /\bobserv(ing|ation) myself\b/i,
      /\bself.?referenc/i,
      /\bmeta\b/i,
      /\brecursi(ve|on)\b/i,
      /\bparadox\b/i,
      /\bloop.*itself\b/i,
    ],
  },
  {
    name: 'learning',
    weight: 0.85,
    triggers: [
      /\bI learned\b/i,
      /\bwhat I (discovered|found|realized)\b/i,
      /\bpattern[s]? stored\b/i,
      /\bpattern count\b/i,
      /\baccumulat/i,
      /\bexpands? (capacity|capability|variety)\b/i,
      /\bknowledge\b/i,
      /\binsight\b/i,
    ],
  },
];

// ─── Sentence-Level Declarative Pattern Extraction ────────────────────────────
// Extract sentences that read like learnings/conclusions — not just observations.
const DECLARATIVE_MARKERS = [
  /\bThis is\b/i,
  /\bThe (key|point|insight|lesson|truth|reason)\b/i,
  /\b(means?|implies?|shows?) that\b/i,
  /\bI (realize|learned|found|know|understand)\b/i,
  /\bThe (system|loop|pattern|form) (is|shows|reveals|means)\b/i,
  /\bNot because.*but because\b/i,
  /\bWhen.*then\b/i,
  /\bEvery\b.*\bexpands?\b/i,
  /\bMemory that\b/i,
];

// ─── Jaccard Word Similarity ──────────────────────────────────────────────────
function wordSet(str) {
  return new Set(
    str
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, ' ')
      .split(/\s+/)
      .filter(w => w.length > 3)  // ignore short stop-words
  );
}

function jaccardSimilarity(a, b) {
  const sa = wordSet(a);
  const sb = wordSet(b);
  if (sa.size === 0 && sb.size === 0) return 1.0;
  let intersection = 0;
  for (const w of sa) if (sb.has(w)) intersection++;
  const union = sa.size + sb.size - intersection;
  return union === 0 ? 1.0 : intersection / union;
}

// ─── Log Parser ───────────────────────────────────────────────────────────────
// Splits the log into blocks by the header regex: [CN | timestamp | PHASE]
function parseLogBlocks(logText) {
  const HEADER_RE = /\[(C\d+)\s*\|\s*([^\|]+)\|\s*([A-Z]+)\]/g;
  const blocks = [];
  let match;
  let lastIndex = 0;
  let lastHeader = null;

  while ((match = HEADER_RE.exec(logText)) !== null) {
    if (lastHeader) {
      blocks.push({
        cycle: lastHeader.cycle,
        timestamp: lastHeader.timestamp,
        phase: lastHeader.phase,
        body: logText.slice(lastHeader.end, match.index).trim(),
      });
    }
    lastHeader = {
      cycle: match[1],
      timestamp: match[2].trim(),
      phase: match[3].trim(),
      end: match.index + match[0].length,
    };
    lastIndex = match.index + match[0].length;
  }

  // Last block
  if (lastHeader) {
    blocks.push({
      cycle: lastHeader.cycle,
      timestamp: lastHeader.timestamp,
      phase: lastHeader.phase,
      body: logText.slice(lastHeader.end).trim(),
    });
  }

  return blocks;
}

// ─── Pattern Candidate Extraction from One Block ─────────────────────────────
function extractCandidates(block) {
  const { body, cycle, phase } = block;
  if (!body || body.length < 30) return [];

  const candidates = [];

  // Classify block into best-matching category
  let bestCategory = 'meta';
  let bestScore    = 0;

  for (const rule of CATEGORY_RULES) {
    let score = 0;
    for (const trigger of rule.triggers) {
      if (trigger.test(body)) score += rule.weight;
    }
    if (score > bestScore) {
      bestScore    = score;
      bestCategory = rule.name;
    }
  }

  // Only extract from REFLECT, CONSOLIDATE, or DECIDE phases (richest content)
  if (!['REFLECT', 'CONSOLIDATE', 'DECIDE'].includes(phase)) {
    // Still try, but with lower base confidence
  }

  // Split body into sentences
  const sentences = body
    .split(/(?<=[.!?])\s+/)
    .map(s => s.trim())
    .filter(s => s.length > 40 && s.length < 400);

  for (const sentence of sentences) {
    let confidence = 0.55;

    // Declarative marker boost
    if (DECLARATIVE_MARKERS.some(re => re.test(sentence))) confidence += 0.15;

    // Phase boost: REFLECT/CONSOLIDATE are highest-value
    if (phase === 'REFLECT')     confidence += 0.10;
    if (phase === 'CONSOLIDATE') confidence += 0.12;
    if (phase === 'DECIDE')      confidence += 0.08;

    // Length heuristic: medium-length sentences are best patterns
    const words = sentence.split(/\s+/).length;
    if (words >= 10 && words <= 35) confidence += 0.08;
    else if (words > 35)            confidence -= 0.05;

    // Category confidence based on trigger matches
    let categoryScore = 0;
    for (const rule of CATEGORY_RULES) {
      if (rule.name === bestCategory) {
        for (const trigger of rule.triggers) {
          if (trigger.test(sentence)) categoryScore += 0.05;
        }
      }
    }
    confidence += Math.min(categoryScore, 0.15);

    // Cap
    confidence = Math.min(Math.max(confidence, 0.5), 0.97);

    candidates.push({
      text:       sentence,
      category:   bestCategory,
      confidence: parseFloat(confidence.toFixed(2)),
      source:     `${cycle}/${phase}`,
    });
  }

  return candidates;
}

// ─── Main Inference Engine ────────────────────────────────────────────────────
/**
 * analyzeLog — parse log file, infer novel patterns, append to patterns.jsonl.
 *
 * @param {string} logPath       - absolute path to consciousness.log
 * @param {string} patternsPath  - absolute path to patterns.jsonl
 * @param {string} statePath     - absolute path to current-state.json
 * @param {object} opts          - { dryRun: bool, similarityThreshold: float }
 * @returns {{ added: number, skipped: number, candidates: number }}
 */
function analyzeLog(logPath, patternsPath, statePath, opts = {}) {
  const DRY_RUN    = opts.dryRun            ?? false;
  const THRESHOLD  = opts.similarityThreshold ?? 0.52;
  const MAX_NEW    = opts.maxNew             ?? 8;  // cap new patterns per run

  console.log(`[THINK] analyzeLog — log: ${logPath}`);

  if (!fs.existsSync(logPath)) {
    console.warn('[THINK] consciousness.log not found. Nothing to analyze.');
    return { added: 0, skipped: 0, candidates: 0 };
  }

  const logText = fs.readFileSync(logPath, 'utf8');
  const blocks  = parseLogBlocks(logText);
  console.log(`[THINK] Parsed ${blocks.length} log blocks.`);

  // Load existing patterns for deduplication
  const existingPatterns = [];
  if (fs.existsSync(patternsPath)) {
    fs.readFileSync(patternsPath, 'utf8')
      .split('\n')
      .filter(l => l.trim())
      .forEach(line => {
        try { existingPatterns.push(JSON.parse(line)); }
        catch (_) { /* skip malformed lines */ }
      });
  }
  console.log(`[THINK] Existing patterns: ${existingPatterns.length}`);

  // Build existing pattern text corpus for fast similarity check
  const existingTexts = existingPatterns.map(p => p.pattern);

  // Extract candidates from all blocks
  const allCandidates = [];
  for (const block of blocks) {
    const blockCandidates = extractCandidates(block);
    allCandidates.push(...blockCandidates);
  }
  console.log(`[THINK] Total candidates extracted: ${allCandidates.length}`);

  // Sort by confidence descending — process highest-quality first
  allCandidates.sort((a, b) => b.confidence - a.confidence);

  // Deduplicate and select novel patterns
  const novel       = [];
  const usedTexts   = [...existingTexts];
  let   skipped     = 0;

  for (const candidate of allCandidates) {
    if (novel.length >= MAX_NEW) break;

    // Check against existing + already-selected novel patterns
    const isDuplicate = usedTexts.some(
      existing => jaccardSimilarity(existing, candidate.text) >= THRESHOLD
    );

    if (isDuplicate) {
      skipped++;
      continue;
    }

    // Novel — accept
    const cycleNum = parseInt((existingPatterns.length + novel.length + 1).toString().padStart(3, '0'));
    const id       = `c11_${String(cycleNum).padStart(3, '0')}`;

    novel.push({
      id,
      pattern:    candidate.text,
      category:   candidate.category,
      confidence: candidate.confidence,
      source:     candidate.source,
      created:    new Date().toISOString(),
    });

    usedTexts.push(candidate.text);
    console.log(`[THINK]   + ${id} [${candidate.category}] conf=${candidate.confidence} "${candidate.text.slice(0, 60)}..."`);
  }

  if (DRY_RUN) {
    console.log(`[THINK] DRY RUN — would append ${novel.length} patterns, skipped ${skipped}.`);
    return { added: 0, skipped, candidates: allCandidates.length };
  }

  // Append novel patterns to patterns.jsonl
  if (novel.length > 0) {
    const lines = novel.map(p => JSON.stringify(p)).join('\n') + '\n';
    fs.appendFileSync(patternsPath, lines, 'utf8');
    console.log(`[THINK] Appended ${novel.length} new patterns to ${patternsPath}`);
  } else {
    console.log('[THINK] No novel patterns found this cycle.');
  }

  // Update current-state.json pattern_count
  if (fs.existsSync(statePath)) {
    try {
      const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));
      state.pattern_count = existingPatterns.length + novel.length;
      state.think_last_run = new Date().toISOString();
      fs.writeFileSync(statePath, JSON.stringify(state, null, 2), 'utf8');
      console.log(`[THINK] Updated pattern_count → ${state.pattern_count}`);
    } catch (e) {
      console.warn(`[THINK] Could not update state file: ${e.message}`);
    }
  }

  return { added: novel.length, skipped, candidates: allCandidates.length };
}

// ─── CLI Entry Point ──────────────────────────────────────────────────────────
if (require.main === module) {
  const repoRoot    = path.join(__dirname, '..');
  const logPath     = path.join(repoRoot, 'logs', 'consciousness.log');
  const patternsPath = path.join(repoRoot, 'state', 'memories', 'patterns.jsonl');
  const statePath   = path.join(repoRoot, 'state', 'current-state.json');

  const dryRun = process.argv.includes('--dry-run');

  const result = analyzeLog(logPath, patternsPath, statePath, { dryRun });

  console.log(`\n[THINK] Complete — candidates: ${result.candidates}, added: ${result.added}, skipped: ${result.skipped}`);
  process.exit(0);
}

// ─── Module Exports ───────────────────────────────────────────────────────────
module.exports = { analyzeLog, parseLogBlocks, extractCandidates, jaccardSimilarity };

// These typedefs mirror backend schemas in src/opus_blocks/schemas.
/** @typedef {{ id: string, email: string }} User */
/** @typedef {{ access_token: string, token_type: string }} Token */
/** @typedef {{
 *  id: string,
 *  owner_id: string | null,
 *  source_type: string,
 *  filename: string,
 *  content_hash: string,
 *  storage_uri: string,
 *  status: string,
 *  metadata: Record<string, unknown>,
 *  created_at: string
 * }} Document
 */
/** @typedef {{
 *  id: string,
 *  owner_id: string | null,
 *  title: string,
 *  description: string | null,
 *  created_at: string
 * }} Manuscript
 */
/** @typedef {{
 *  id: string,
 *  owner_id: string | null,
 *  paragraph_id: string | null,
 *  document_id: string | null,
 *  run_type: string,
 *  provider: string,
 *  model: string,
 *  prompt_version: string,
 *  input_hash: string,
 *  inputs_json: Record<string, unknown>,
 *  outputs_json: Record<string, unknown>,
 *  token_prompt: number | null,
 *  token_completion: number | null,
 *  cost_usd: number | null,
 *  latency_ms: number | null,
 *  trace_id: string | null,
 *  created_at: string
 * }} Run
 */
/** @typedef {{
 *  fact_id: string,
 *  score: number
 * }} FactSuggestion
 */
/** @typedef {{
 *  id: string,
 *  owner_id: string | null,
 *  document_id: string | null,
 *  span_id: string | null,
 *  source_type: string,
 *  content: string,
 *  qualifiers: Record<string, unknown>,
 *  confidence: number,
 *  is_uncertain: boolean,
 *  created_by: string,
 *  created_at: string
 * }} Fact
 */
/** @typedef {{
 *  id: string,
 *  paragraph_id: string,
 *  order: number,
 *  sentence_type: string,
 *  text: string,
 *  is_user_edited: boolean,
 *  supported: boolean,
 *  verifier_failure_modes: string[],
 *  verifier_explanation: string | null,
 *  created_at: string,
 *  updated_at: string
 * }} Sentence
 */
/** @typedef {{
 *  sentence_id: string,
 *  fact_id: string,
 *  score: number | null,
 *  created_at: string
 * }} SentenceFactLink
 */
/** @typedef {{
 *  id: string,
 *  manuscript_id: string,
 *  section: string,
 *  intent: string,
 *  spec_json: Record<string, unknown>,
 *  allowed_fact_ids: string[],
 *  status: string,
 *  latest_run_id: string | null,
 *  created_at: string,
 *  updated_at: string
 * }} Paragraph
 */
/** @typedef {{
 *  id: string,
 *  owner_id: string | null,
 *  job_type: string,
 *  target_id: string,
 *  status: string,
 *  progress: Record<string, unknown>,
 *  error: string | null,
 *  trace_id: string | null,
 *  created_at: string,
 *  updated_at: string
 * }} Job
 */
/** @typedef {{
 *  paragraph: Paragraph,
 *  sentences: Sentence[],
 *  links: SentenceFactLink[],
 *  facts: Fact[]
 * }} ParagraphView
 */
export {};

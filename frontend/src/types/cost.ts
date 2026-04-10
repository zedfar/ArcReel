/** Detail biaya: Mata uang → Pemetaan jumlah */
export type CostBreakdown = Record<string, number>;

/** Biaya berdasarkan tipe */
export interface CostByType {
  image?: CostBreakdown;
  video?: CostBreakdown;
  character_and_clue?: CostBreakdown;
}

/** Biaya per segmen */
export interface SegmentCost {
  segment_id: string;
  duration_seconds: number;
  estimate: { image: CostBreakdown; video: CostBreakdown };
  actual: { image: CostBreakdown; video: CostBreakdown };
}

/** Biaya per episode */
export interface EpisodeCost {
  episode: number;
  title: string;
  segments: SegmentCost[];
  totals: { estimate: CostByType; actual: CostByType };
}

/** Informasi Model */
export interface ModelInfo {
  provider: string;
  model: string;
}

/** Respons API estimasi biaya */
export interface CostEstimateResponse {
  project_name: string;
  models: { image: ModelInfo; video: ModelInfo };
  episodes: EpisodeCost[];
  project_totals: { estimate: CostByType; actual: CostByType };
}

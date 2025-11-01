export type SegmentBucket = { label: string; A: number; B: number; tie: number };
export type Segment = { name: string; buckets: SegmentBucket[] };
export type Reason = { driver: string; summary: string; evidence: string[] };
export type Drivers = {
  price_value: { payable_A: number; payable_B: number; coupon_usable_A: boolean; coupon_usable_B: boolean };
  delivery: { eta_A_p50: number; eta_B_p50: number };
  trust: { rating_A: number; reviews_A: number; rating_B: number; reviews_B: number };
  fit: { cuisine_match_A: number; cuisine_match_B: number };
};
export type ExperimentResult = {
  experiment_id: string;
  city: string;
  cohort: Record<string, string>;
  sample_n: number;
  aggregate: { A: number; B: number; tie: number; confidence: 'low' | 'medium' | 'high' };
  top_reasons: Reason[];
  segments: Segment[];
  drivers: Drivers;
  recommended_actions: string[];
  twins: { id: string; winner: 'A' | 'B' | 'tie'; reason: string }[];
};


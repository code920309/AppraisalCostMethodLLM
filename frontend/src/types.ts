export interface BuildingInfo {
  address: string;
  structure: string;
  totalArea: number; // in m2
  approvalDate: string; // YYYY-MM-DD
  age: number;
  floors: number;
  panoramaImage?: string;
}

export interface Defect {
  type: 'crack' | 'efflorescence' | 'corrosion' | 'leakage';
  severity: number; // 0 to 1
  description: string;
  location?: string;
}

export interface AppraisalResult {
  replacementCost: number;
  physicalDepreciation: number;
  observationDepreciation: number;
  totalDepreciation: number;
  finalValue: number;
  depreciationRate: number;
}

export interface AppraisalReport {
  buildingInfo: BuildingInfo;
  defects: Defect[];
  result: AppraisalResult;
  aiOpinion: string;
}

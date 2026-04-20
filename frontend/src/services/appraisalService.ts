import axios from 'axios';
import { AppraisalResult, BuildingInfo, Defect } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const appraisalService = {
  async getBuildingInfo(address: string): Promise<BuildingInfo | null> {
    try {
      // 1. Search for address to get codes
      console.info("[API Request] Searching address:", address);
      const searchRes = await axios.get(`${API_BASE_URL}/registry/search`, { params: { q: address } });
      const results = searchRes.data.results;
      console.info("[API Response] Address search results:", results);
      
      if (!results || results.length === 0) {
        console.warn("[API Warning] No address results found.");
        return null;
      }
      
      const first = results[0];
      // 2. Get building info using codes
      console.info("[API Request] Fetching building info for:", first.address_name);
      const infoRes = await axios.get(`${API_BASE_URL}/registry/info`, {
        params: {
          sigunguCd: first.bcode.substring(0, 5),
          bjdongCd: first.bcode.substring(5),
          bun: first.main_address_no,
          ji: first.sub_address_no,
          lat: first.lat,
          lon: first.lon
        }
      });
      
      const data = infoRes.data;
      console.info("[API Response] Building official data raw:", data);
      
      const currentYear = new Date().getFullYear();
      let approvalYear = currentYear;
      
      if (data.useAprvDe) {
        const dateStr = String(data.useAprvDe);
        const yearPart = dateStr.substring(0, 4);
        approvalYear = parseInt(yearPart) || currentYear;
        console.info(`[Calculation] Parsed Year: ${yearPart}, Approval Year: ${approvalYear}, Current: ${currentYear}`);
      } else {
        console.warn("[Calculation Warning] useAprvDe is missing or empty.");
      }
      
      const mappedInfo: BuildingInfo = {
        address: first.address_name,
        structure: data.strctCdNm,
        totalArea: data.totArea,
        approvalDate: data.useAprvDe,
        age: currentYear - approvalYear,
        floors: data.grndFlrCnt, // API에서 받아온 지상층수 반영
        panoramaImage: data.panorama_image,
      };
      
      console.info("[Frontend Mapped] Building info for UI:", mappedInfo);
      return mappedInfo;
    } catch (error) {
      console.error("[API Error] Failed to fetch building info:", error);
      return null;
    }
  },

  async calculateAppraisal(building: BuildingInfo, defects: Defect[]): Promise<AppraisalResult | null> {
    try {
      const defectObj = defects[0] || { severity: 0, type: 'crack' };
      
      const payload = {
        address: building.address,
        total_area: building.totalArea,
        usage_name: building.structure,
        elapsed_years: building.age,
        defect_ratio: defectObj.severity,
        severity: defectObj.severity > 0.08 ? "심각" : defectObj.severity > 0.02 ? "경구" : defectObj.severity > 0 ? "주의" : "정상",
        confidence: 0.95
      };

      console.info("[Calculation API Request] Sending data to server:", payload);

      const response = await axios.post(`${API_BASE_URL}/appraisal/calculate`, payload);

      const data = response.data;
      console.info("[Calculation API Response] Received from server:", data);

      return {
        replacementCost: data.replacement_cost,
        physicalDepreciation: data.physical_depreciation,
        observationDepreciation: data.observation_depreciation,
        totalDepreciation: data.total_depreciation,
        finalValue: data.final_value,
        depreciationRate: data.depreciation_rate,
      };
    } catch (error) {
      console.error("Appraisal Calculation API Error:", error);
      return null;
    }
  }
};

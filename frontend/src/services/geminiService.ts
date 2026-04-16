import axios from 'axios';
import { BuildingInfo, Defect } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface AnalysisResponse {
  defects: Defect[];
  imageData: string;
}

export const geminiService = {
  async analyzeDefects(imageBase64: string): Promise<AnalysisResponse | null> {
    try {
      const byteString = atob(imageBase64);
      const ab = new ArrayBuffer(byteString.length);
      const ia = new Uint8Array(ab);
      for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
      }
      const blob = new Blob([ab], { type: 'image/jpeg' });
      const file = new File([blob], "image.jpg", { type: 'image/jpeg' });

      const formData = new FormData();
      formData.append('file', file);

      console.info("[API Request] Sending image for defect analysis...", { fileName: file.name, fileSize: file.size });
      const response = await axios.post(`${API_BASE_URL}/analysis/detect`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const data = response.data;
      console.info("[API Response] Defect analysis complete:", data.severity, data.defect_ratio);
      
      return {
        defects: [{
          type: 'crack',
          severity: data.defect_ratio,
          description: `결함률: ${(data.defect_ratio * 100).toFixed(2)}%, 신뢰도: ${(data.confidence * 100).toFixed(2)}%`
        }],
        imageData: data.image_data
      };
    } catch (error) {
      console.error("Vision Analysis API Error:", error);
      return null;
    }
  },

  async generateReport(buildingInfo: BuildingInfo, defects: Defect[], appraisalValue: number): Promise<string> {
    try {
      const defectObj = defects[0] || { severity: 0 };
      
      console.info("[API Request] Generating AI Appraisal Report...");
      const response = await axios.post(`${API_BASE_URL}/appraisal/report`, {
        address: buildingInfo.address,
        total_area: buildingInfo.totalArea,
        usage_name: buildingInfo.structure,
        elapsed_years: buildingInfo.age,
        defect_ratio: defectObj.severity,
        severity: defectObj.severity > 0.08 ? "심각" : defectObj.severity > 0.02 ? "경구" : defectObj.severity > 0 ? "주의" : "정상",
        confidence: 0.95,
        is_official_data: true
      });

      const data = response.data;
      return response.data.report || "리포트 생성 실패";
    } catch (error) {
      console.error("Appraisal Report API Error:", error);
      return "리포트 생성 중 오류가 발생했습니다.";
    }
  },

  async exportPdf(
    buildingInfo: BuildingInfo, 
    defects: Defect[], 
    llmContent: string, 
    appraisalValue: number,
    replacementCost: number,
    physicalDepreciation: number,
    observationDepreciation: number,
    mainImage?: string,
    defectImage?: string
  ): Promise<void> {
    try {
      const defectObj = defects[0] || { severity: 0 };
      const response = await axios.post(`${API_BASE_URL}/appraisal/export/pdf`, {
        address: buildingInfo.address,
        total_area: buildingInfo.totalArea,
        usage_name: buildingInfo.structure,
        elapsed_years: buildingInfo.age,
        defect_ratio: defectObj.severity,
        severity: defectObj.severity > 0.08 ? "심각" : defectObj.severity > 0.02 ? "경구" : defectObj.severity > 0 ? "주의" : "정상",
        confidence: 0.95,
        llm_content: llmContent,
        total_value: appraisalValue,
        replacement_cost: replacementCost,
        physical_depreciation: physicalDepreciation,
        observation_depreciation: observationDepreciation,
        main_image: mainImage || "",
        defect_image: defectImage || ""
      }, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `appraisal_report_${buildingInfo.address.replace(/\s/g, '_')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("PDF Export Error:", error);
      alert("PDF 내보내기 중 오류가 발생했습니다.");
    }
  }
};

import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const registryApi = {
  searchAddress: (q: string) => api.get('/registry/search', { params: { q } }),
  getBuildingInfo: (params: { sigunguCd: str; bjdongCd: str; bun: str; ji: str }) => 
    api.get('/registry/info', { params }),
};

export const analysisApi = {
  detectDefects: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/analysis/detect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const appraisalApi = {
  createReport: (data: any) => api.post('/appraisal/report', data),
};

export default api;

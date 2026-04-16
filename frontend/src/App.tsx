/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useCallback } from 'react';
import { 
  Search, 
  Building2, 
  Camera, 
  FileText, 
  AlertTriangle, 
  TrendingDown, 
  Calculator,
  MapPin,
  Calendar,
  Layers,
  ArrowRight,
  Download,
  CheckCircle2,
  Loader2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell,
  PieChart,
  Pie
} from 'recharts';

import { Card, Button, Input } from './components/UI';
import { BuildingInfo, Defect, AppraisalResult } from './types';
import { appraisalService } from './services/appraisalService';
import { geminiService } from './services/geminiService';
import { formatCurrency, cn } from './lib/utils';
import { MOCK_BUILDINGS } from './constants';

export default function App() {
  const [address, setAddress] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [building, setBuilding] = useState<BuildingInfo | null>(null);
  const [defects, setDefects] = useState<Defect[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [appraisal, setAppraisal] = useState<AppraisalResult | null>(null);
  const [report, setReport] = useState<string | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [analyzedImage, setAnalyzedImage] = useState<string | null>(null);
  const [lastSynced, setLastSynced] = useState<string | null>(null);

  React.useEffect(() => {
    if (building) {
      console.info("[UI State Update] Building Info synced to UI:", building);
      setLastSynced(new Date().toLocaleTimeString());
    }
  }, [building]);

  React.useEffect(() => {
    if (appraisal) {
      console.info("[UI State Update] Appraisal Result synced to UI:", appraisal);
    }
  }, [appraisal]);

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!address) return;

    setIsLoading(true);
    setBuilding(null);
    setDefects([]);
    setAppraisal(null);
    setReport(null);

    try {
      const info = await appraisalService.getBuildingInfo(address);
      if (info) {
        setBuilding(info);
        const initialResult = await appraisalService.calculateAppraisal(info, []);
        if (initialResult) setAppraisal(initialResult);
      } else {
        // API 서버 장애 시 테스트를 위해 샘플 데이터로 강제 진행
        console.warn("[Fallback] API 서버 응답 지연으로 인해 샘플 데이터로 전환합니다.");
        const fallbackInfo: BuildingInfo = {
          address: address,
          structure: '철근콘크리트구조',
          totalArea: 500,
          approvalDate: '1995-01-01',
          age: 31,
          floors: 5,
          panoramaImage: undefined
        };
        setBuilding(fallbackInfo);
        const initialResult = appraisalService.calculateAppraisal(fallbackInfo, []);
        setAppraisal(initialResult);
        alert('공공데이터 API 서버 응답이 지연되어 샘플 데이터로 진행합니다. (사진 업로드 가능)');
      }
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !building) return;

    setIsAnalyzing(true);
    
    try {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64 = (reader.result as string).split(',')[1];
        const result = await geminiService.analyzeDefects(base64);
        
        if (result) {
          const updatedDefects = [...defects, ...result.defects];
          setDefects(updatedDefects);
          setAnalyzedImage(result.imageData);
          
          const updatedResult = await appraisalService.calculateAppraisal(building, updatedDefects);
          if (updatedResult) {
            setAppraisal(updatedResult);
            
            // 이미지 분석 완료 후 자동으로 AI 리포트 생성 시작
            console.info("[Workflow] Auto-triggering AI Report generation...");
            setIsGeneratingReport(true);
            try {
              const aiReport = await geminiService.generateReport(building, updatedDefects, updatedResult.finalValue);
              setReport(aiReport);
            } catch (err) {
              console.error("Auto Report failed:", err);
            } finally {
              setIsGeneratingReport(false);
            }
          }
        }
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error(error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!building || !appraisal) return;

    setIsGeneratingReport(true);
    try {
      const aiReport = await geminiService.generateReport(building, defects, appraisal.finalValue);
      setReport(aiReport);
    } catch (error) {
      console.error(error);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const handleExportPdf = async () => {
    if (!building || !report || !appraisal) {
      alert("먼저 리포트를 생성하고 감정가액 산출을 완료해주십시오.");
      return;
    }
    await geminiService.exportPdf(
      building, 
      defects, 
      report, 
      appraisal.finalValue,
      appraisal.replacementCost,
      appraisal.physicalDepreciation,
      appraisal.observationDepreciation,
      building.panoramaImage,
      analyzedImage || undefined
    );
  };

  const chartData = appraisal ? [
    { name: '재조달원가', value: appraisal.replacementCost },
    { name: '물리적감가', value: appraisal.physicalDepreciation },
    { name: '관찰감가', value: appraisal.observationDepreciation },
    { name: '적산가액', value: appraisal.finalValue },
  ] : [];

  const pieData = appraisal ? [
    { name: '적산가액', value: appraisal.finalValue, color: '#4f46e5' },
    { name: '감가액', value: appraisal.totalDepreciation, color: '#ef4444' },
  ] : [];

  return (
    <div className="h-screen bg-brand-bg text-brand-text-main font-sans flex flex-col overflow-hidden">
      {/* Header */}
      <header className="h-[60px] bg-brand-header text-white flex items-center px-6 justify-between border-b-3 border-brand-accent shrink-0">
        <div className="flex items-center gap-2">
          <div className="font-extrabold text-xl tracking-tighter">
            AppraisalCost<span className="text-brand-accent ml-1">AI</span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <form onSubmit={handleSearch} className="relative group">
            <div className="bg-white/10 px-4 py-2 rounded-md border border-white/20 w-[400px] flex items-center focus-within:bg-white/20 transition-all">
              <Search className="text-white/50" size={16} />
              <input 
                className="bg-transparent border-none text-white ml-2 w-full outline-none text-sm placeholder:text-white/30"
                placeholder="서울특별시 강남구 테헤란로 123"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </div>
          </form>
          <div className="bg-white/10 px-3 py-1 rounded text-[0.7rem] font-bold uppercase tracking-wider text-white/70">
            User: K. Appraiser
          </div>
        </div>
      </header>

      <main className="flex-1 grid grid-cols-[300px_1fr_320px] gap-[1px] bg-brand-border overflow-hidden">
        <AnimatePresence mode="wait">
          {!building ? (
            <motion.div 
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="col-span-3 flex flex-col items-center justify-center bg-white"
            >
              <div className="w-16 h-16 bg-brand-bg rounded-full flex items-center justify-center mb-4">
                <Building2 className="text-brand-text-sub w-8 h-8" />
              </div>
              <h2 className="text-lg font-bold text-brand-text-main">감정 대상을 검색하세요</h2>
              <p className="text-brand-text-sub max-w-sm mt-1 text-center text-sm">주소를 입력하면 건축물대장 정보와 스트릿 뷰를 자동으로 불러와 탁상감정을 시작합니다.</p>
              <div className="mt-6 flex gap-2">
                {Object.keys(MOCK_BUILDINGS).map((addr) => (
                  <Button 
                    key={addr}
                    variant="outline"
                    size="sm"
                    onClick={() => { setAddress(addr); handleSearch(); }}
                  >
                    {addr}
                  </Button>
                ))}
              </div>
            </motion.div>
          ) : (
            <>
              {/* Left Panel: Property Info */}
              <section className="bg-white p-5 overflow-y-auto flex flex-col gap-6">
                <div>
                  <div className="panel-title">
                    <span>건물 기본 정보</span>
                    <span className="flex items-center gap-1">
                      <div className="w-1.5 h-1.5 bg-brand-success rounded-full animate-pulse" />
                      SYNCED {lastSynced}
                    </span>
                  </div>
                    <div className="w-full h-[180px] bg-slate-200 rounded-lg mb-4 relative overflow-hidden">
                      <img 
                        src={building.panoramaImage ? `data:image/jpeg;base64,${building.panoramaImage}` : `https://picsum.photos/seed/${encodeURIComponent(building.address)}/600/400`} 
                        alt="Street View" 
                        className="w-full h-full object-cover"
                        referrerPolicy="no-referrer"
                      />
                    <div className="absolute bottom-2 left-2 bg-black/60 text-white px-2 py-1 text-[0.7rem] rounded">
                      Google Street View (2024.01)
                    </div>
                  </div>
                  <div className="grid gap-3">
                    <div className="data-item">
                      <label>건물 구조</label>
                      <value>{building.structure}</value>
                    </div>
                    <div className="data-item">
                      <label>연면적 / 층수</label>
                      <value>{building.totalArea.toLocaleString()} m² / 지상 {building.floors}층</value>
                    </div>
                    <div className="data-item">
                      <label>사용승인일 (경과연수)</label>
                      <value>{building.approvalDate} ({building.age}년)</value>
                    </div>
                    <div className="data-item">
                      <label>건물 노후 등급</label>
                      <value>
                        <span className={cn(
                          "px-2 py-0.5 rounded text-[0.7rem] font-bold",
                          building.age > 20 ? "bg-amber-100 text-amber-800" : "bg-green-100 text-green-800"
                        )}>
                          {building.age > 20 ? "보통 (B)" : "우수 (A)"}
                        </span>
                      </value>
                    </div>
                  </div>
                </div>

                <div className="mt-auto p-4 bg-brand-bg rounded-lg border border-brand-border">
                  <div className="text-[0.7rem] text-brand-text-sub mb-1">공공데이터포털 연동</div>
                  <div className="text-[0.8rem] font-bold text-brand-success flex items-center gap-1">
                    <CheckCircle2 size={14} /> 건축물대장 조회 완료
                  </div>
                </div>
              </section>

              {/* Center Panel: Vision Analysis */}
              <section className="bg-slate-100 p-5 flex flex-col overflow-hidden">
                <div className="panel-title">
                  <span>AI 결함 탐지 분석</span>
                  <span>YOLOv8 VISION</span>
                </div>
                
                <div className="flex-1 bg-[#0F172A] rounded-xl relative overflow-hidden flex items-center justify-center">
                  {isAnalyzing ? (
                    <div className="flex flex-col items-center text-white/50">
                      <Loader2 className="animate-spin mb-2" size={32} />
                      <span className="text-xs font-bold uppercase tracking-widest">Analyzing...</span>
                    </div>
                  ) : defects.length > 0 ? (
                    <div className="w-full h-full relative">
                      <img 
                        src={analyzedImage ? `data:image/jpeg;base64,${analyzedImage}` : `https://picsum.photos/seed/defect-${building.address}/1200/800`} 
                        className="w-full h-full object-cover"
                        referrerPolicy="no-referrer"
                      />
                      {/* Mock Defect Boxes */}
                      {defects.map((d, i) => (
                        <div 
                          key={i}
                          className="absolute border-2 border-brand-danger bg-brand-danger/10"
                          style={{
                            top: `${20 + (i * 25)}%`,
                            left: `${15 + (i * 20)}%`,
                            width: '120px',
                            height: '80px'
                          }}
                        >
                          <div className="absolute -top-5 -left-[2px] bg-brand-danger text-white text-[10px] px-1 font-bold uppercase">
                            {d.type}: {d.severity.toFixed(2)}
                          </div>
                        </div>
                      ))}

                      <div className="absolute top-5 right-5 w-[200px] bg-slate-900/80 backdrop-blur-md rounded-lg p-4 text-white border border-white/10">
                        <div className="font-bold text-xs mb-3 border-b border-white/20 pb-2 uppercase tracking-wider">분석 리포트</div>
                        <div className="flex justify-between text-[0.75rem] mb-2">
                          <span className="text-white/50">결함 수</span>
                          <span className="font-bold">{defects.length}개</span>
                        </div>
                        <div className="flex justify-between text-[0.75rem] mb-2">
                          <span className="text-white/50">최대 심각도</span>
                          <span className="font-bold text-brand-danger">{(Math.max(...defects.map(d => d.severity)) * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex justify-between text-[0.75rem]">
                          <span className="text-white/50">노후 가속도</span>
                          <span className="font-bold text-amber-400">+{ (defects.length * 0.5).toFixed(1) }%</span>
                        </div>
                        <div className="mt-3 text-[0.65rem] text-white/40 italic">
                          관찰감가 보정치 산출 완료
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center text-white/20">
                      <Camera size={48} className="mb-4" />
                      <span className="text-xs font-bold uppercase tracking-widest">No Data Uploaded</span>
                    </div>
                  )}
                </div>

                <div className="mt-4 flex gap-3">
                  <div className="flex-1">
                    <input 
                      type="file" 
                      id="vision-upload" 
                      className="hidden" 
                      accept="image/*"
                      onChange={handleImageUpload}
                    />
                    <label htmlFor="vision-upload" className="block h-full">
                      <div className="h-16 border-2 border-dashed border-brand-border rounded-lg flex items-center justify-center text-brand-text-sub text-sm font-medium hover:border-brand-accent hover:text-brand-accent transition-all cursor-pointer bg-white/50">
                        이미지 추가 업로드
                      </div>
                    </label>
                  </div>
                  <div className="flex-1 h-16 border-2 border-dashed border-brand-border rounded-lg flex items-center justify-center text-brand-text-sub text-sm font-medium bg-white/50">
                    전경 사진 재촬영
                  </div>
                </div>
              </section>

              {/* Right Panel: Appraisal */}
              <section className="bg-white p-5 flex flex-col overflow-y-auto">
                <div className="panel-title">
                  <span>원가법 탁상감정</span>
                  <span>AUTOMATED</span>
                </div>

                {appraisal && (
                  <div className="flex flex-col flex-1">
                    <div className="grid gap-2 mb-6">
                      <div className="flex justify-between text-sm py-2 border-b border-brand-bg">
                        <label className="text-brand-text-sub">표준 신축 단가</label>
                        <span className="mono font-bold">₩{(appraisal.replacementCost / building.totalArea).toLocaleString()} /㎡</span>
                      </div>
                      <div className="flex justify-between text-sm py-2 border-b border-brand-bg">
                        <label className="text-brand-text-sub">재조달원가</label>
                        <span className="mono font-bold">{formatCurrency(appraisal.replacementCost)}</span>
                      </div>
                      <div className="flex justify-between text-sm py-2 border-b border-brand-bg">
                        <label className="text-brand-text-sub">물리적 감가</label>
                        <span className="mono font-bold text-brand-danger">-{formatCurrency(appraisal.physicalDepreciation)}</span>
                      </div>
                      <div className="flex justify-between text-sm py-2 border-b border-brand-bg">
                        <label className="text-brand-text-sub">AI 관찰감가 보정</label>
                        <span className="mono font-bold text-brand-danger">-{formatCurrency(appraisal.observationDepreciation)}</span>
                      </div>
                      <div className="flex justify-between text-sm py-2 border-b border-brand-bg">
                        <label className="text-brand-text-sub">기타 보정치</label>
                        <span className="mono font-bold">1.00</span>
                      </div>
                      <div className="flex justify-between items-end pt-4 mt-2 border-t-2 border-brand-text-main">
                        <label className="font-bold text-sm">최종 적산가액</label>
                        <span className="mono text-xl font-black text-brand-accent">{formatCurrency(appraisal.finalValue)}</span>
                      </div>
                    </div>

                    <div className="mb-6">
                      <div className="text-[0.75rem] text-brand-text-sub mb-2 font-bold uppercase">Gemini AI 의견 요약</div>
                      <div className="bg-brand-bg p-4 rounded-lg text-sm leading-relaxed text-brand-text-main border border-brand-border min-h-[100px]">
                        {isGeneratingReport ? (
                          <div className="flex items-center gap-2 text-brand-text-sub">
                            <Loader2 className="animate-spin" size={14} /> 작성 중...
                          </div>
                        ) : report ? (
                          report.slice(0, 200) + '...'
                        ) : (
                          <span className="text-brand-text-sub italic">감정 의견을 생성하려면 아래 버튼을 클릭하세요.</span>
                        )}
                      </div>
                    </div>

                    <div className="mt-auto space-y-3">
                      <Button 
                        className="w-full py-4 flex items-center justify-center gap-2" 
                        onClick={handleExportPdf} 
                        disabled={!report || isGeneratingReport}
                      >
                        <Download size={18} />
                        PDF 리포트 다운로드
                      </Button>
                      <Button 
                        variant="secondary" 
                        className="w-full py-4"
                        onClick={handleGenerateReport}
                        disabled={!appraisal || isGeneratingReport}
                      >
                        {isGeneratingReport ? "리포트 생성 중..." : "AI 리포트 재생성 요청"}
                      </Button>
                    </div>
                  </div>
                )}
              </section>
            </>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

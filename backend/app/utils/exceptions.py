class AppraisalError(Exception):
    """애플리케이션 기본 예외 클래스"""
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details

class APIConnectionError(AppraisalError):
    """외부 API 연결 실패 시 발생"""
    pass

class DataNotFoundError(AppraisalError):
    """필요한 데이터를 찾을 수 없을 때 발생"""
    pass

class VisionAnalysisError(AppraisalError):
    """비전 분석 엔진 오류 시 발생"""
    pass

class LLMServiceError(AppraisalError):
    """LLM 리포트 생성 실패 시 발생"""
    pass

class ValidationError(AppraisalError):
    """데이터 유효성 검사 실패 시 발생"""
    pass

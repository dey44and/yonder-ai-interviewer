from controllers.interview_controller import InterviewController
from services.textanalysis_service import TextAnalysisService

if __name__ == "__main__":
    interview_controller = InterviewController()
    interview_controller.run()

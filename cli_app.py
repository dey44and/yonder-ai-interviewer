"""
Simple CLI app example.
"""

from controllers.cli_interview_controller import CLIInterviewController
from services.textanalysis_service import TextAnalysisService

if __name__ == "__main__":
    interview_controller = CLIInterviewController()
    interview_controller.run()

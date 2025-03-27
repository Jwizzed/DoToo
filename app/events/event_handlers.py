import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_todo_creation_notification(email_to: str, todo_title: str):
    """
    Simulates sending an email notification for new Todo creation.
    """
    logger.info(f"--- Sending TODO notification to {email_to} ---")
    logger.info(f"Subject: New Todo Created!")
    logger.info(f"Body: Your new todo item '{todo_title}' has been successfully created.")
    logger.info(f"--- TODO Notification simulated ---")


async def send_welcome_email(email_to: str, username: str):
    """
    Simulates sending a welcome email to a newly registered user.
    """
    logger.info(f"--- Sending WELCOME email to {email_to} ---")
    logger.info(f"Subject: Welcome to Todo App, {username}!")
    logger.info(f"Body: Hi {username}, thank you for registering at our Todo Application.")
    logger.info(f"We hope you enjoy using the service!")
    logger.info(f"--- WELCOME Email simulated ---")

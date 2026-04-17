from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()

from nova_adk_agent.agents import root_agent


def main() -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="nova-adk-podcast",
        session_service=session_service,
    )
    session = session_service.create_session_sync(
        app_name="nova-adk-podcast",
        user_id="local",
    )
    print("Nova podcast synthesizer. Share a YouTube URL to get started. Ctrl-C to exit.\n")
    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        message = genai_types.Content(
            role="user", parts=[genai_types.Part(text=user_input)]
        )
        for event in runner.run(
            user_id="local",
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if part.text:
                        print(f"agent> {part.text}")


if __name__ == "__main__":
    main()

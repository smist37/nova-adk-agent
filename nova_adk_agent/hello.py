"""Hello-world ADK agent — minimum viable single-agent with one tool.

Run: python -m nova_adk_agent.hello
Then type a question like: "What's 23 * 47?"
"""
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()


def calculator(expression: str) -> dict:
    """Evaluate a basic arithmetic expression. Returns {result: ...} or {error: ...}."""
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return {"error": "Only digits and + - * / ( ) . allowed."}
    try:
        return {"result": eval(expression, {"__builtins__": {}}, {})}
    except Exception as exc:
        return {"error": str(exc)}


root_agent = Agent(
    name="hello_agent",
    model="gemini-2.5-flash",
    description="A minimal ADK agent with one calculator tool.",
    instruction=(
        "You are a helpful assistant. When the user asks a math question, "
        "use the calculator tool. Otherwise answer directly."
    ),
    tools=[calculator],
)


def main() -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="nova-adk-hello",
        session_service=session_service,
    )
    session = session_service.create_session_sync(
        app_name="nova-adk-hello",
        user_id="local",
    )
    print("Hello-world ADK agent. Ctrl-C to exit.\n")
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

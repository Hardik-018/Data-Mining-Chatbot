        "content": user_display
    })

    history.append({
        "role": "assistant",
        "content": str(answer)
    })

    return history, "", None

# ==========================================
# 3. CREATE THE GRADIO APP
# ==========================================

# Gradio 6: do not pass theme/css to Blocks()
with gr.Blocks(
    theme=gr.themes.Base(primary_hue="orange", secondary_hue="stone", neutral_hue="stone"),
    css=CUSTOM_CSS,
    head="""<title>Hardik's Data Mining Chatbot</title><meta name="viewport" content="width=device-width, initial-scale=1">"""
) as demo:

    gr.HTML("""
    <div class="hero">
        <div class="brand-mark">🤖</div>
        <h1>Hardik's Chatbot<br>On Data Mining</h1>
        <p>Your study assistant for concepts, numericals
        and exam preparation.</p>
    </div>
    """)

    gr.HTML("""
    <div class="greeting">
        👋 Hi! I'm your Data Mining study buddy.
        Ask questions from your notes or upload an image.
    </div>
    """)

    mode = gr.Dropdown(
        choices=STUDY_MODES,
        value="Exam Answer",
        label="Study Mode"
    )

    # Removed type="messages" for compatibility
    chatbot = gr.Chatbot(
        height=460,
        label="Chatbot",
        elem_id="chat-window"
    )

    image_input = gr.Image(
        type="filepath",
        label="📷 Upload a question image (optional)",
        sources=["upload"],
        height=190
    )

    with gr.Row():
        message = gr.Textbox(
            placeholder="Ask anything about Data Mining...",
            label="Your question",
            show_label=False,
            lines=1,
            max_lines=5,
            scale=8,
            container=False
        )

        submit_btn = gr.Button(
            "↑",
            variant="primary",
            elem_id="send-question",
            scale=0,
            min_width=48
        )

    clear_btn = gr.Button("Clear Chat")

    gr.HTML("""
    <div class="footer">
        Made by Hardik · Amity Business School
    </div>
    """)

    submit_btn.click(
        fn=respond,
        inputs=[message, chatbot, mode, image_input],
        outputs=[chatbot, message, image_input]
    )

    message.submit(
        fn=respond,
        inputs=[message, chatbot, mode, image_input],
        outputs=[chatbot, message, image_input]
    )

    clear_btn.click(
        fn=lambda: ([], "", None),
        inputs=[],
        outputs=[chatbot, message, image_input]
    )

print("Chatbot UI created successfully.")
print("The demo app is ready.")
# Render supplies PORT. Do not create a temporary Gradio share link in production.
demo.queue(default_concurrency_limit=3, max_size=20)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        share=False,
        show_error=True,
    )

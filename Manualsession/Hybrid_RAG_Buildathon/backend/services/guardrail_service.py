def apply_guardrails(answer, context):
    """
    Validate the LLM answer against the retrieved context.
    """

    # Guardrail 1:
    # Make sure the LLM returned an answer
    if not answer or not answer.strip():
        return {
            "allowed": False,
            "answer": "I could not generate an answer from the provided document."
        }

    # Guardrail 2:
    # Make sure retrieved context exists
    if not context or not context.strip():
        return {
            "allowed": False,
            "answer": "I don't have enough information in the provided document."
        }

    # Guardrail 3:
    # Detect when the LLM itself indicates that
    # the answer is not available in the document
    refusal_phrases = [
        "i don't have enough information",
        "i do not have enough information",
        "not available in the provided document",
        "not mentioned in the provided document",
        "not provided in the document",
        "cannot answer from the provided document"
    ]

    answer_lower = answer.lower()

    for phrase in refusal_phrases:
        if phrase in answer_lower:
            return {
                "allowed": False,
                "answer": "I don't have enough information in the provided document."
            }

    # Guardrail 4:
    # Detect uncertain / unsupported language
    uncertainty_phrases = [
        "i don't know",
        "i am not sure",
        "i cannot verify",
        "according to my knowledge",
        "as far as i know"
    ]

    for phrase in uncertainty_phrases:
        if phrase in answer_lower:
            return {
                "allowed": False,
                "answer": "I don't have enough information in the provided document."
            }

    # All guardrails passed
    return {
        "allowed": True,
        "answer": answer
    }
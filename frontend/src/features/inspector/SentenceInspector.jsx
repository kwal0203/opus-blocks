function SentenceInspector({ activeSentence }) {
  return (
    <div>
      <span className="inspector__label">Active Sentence</span>
      {activeSentence ? (
        <>
          <p className="inspector__value">{activeSentence.text}</p>
          <p className="muted">
            {activeSentence.supported ? "Verified" : "Needs review"} ·{" "}
            {activeSentence.sentence_type}
          </p>
          {activeSentence.verifier_explanation ? (
            <p className="muted">{activeSentence.verifier_explanation}</p>
          ) : null}
        </>
      ) : (
        <p className="muted">Select a sentence to inspect.</p>
      )}
    </div>
  );
}

export default SentenceInspector;

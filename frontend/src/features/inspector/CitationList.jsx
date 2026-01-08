import Badge from "../../components/ui/Badge";
import Card from "../../components/ui/Card";

function CitationList({ paragraphView, activeSentenceId }) {
  if (!paragraphView || !activeSentenceId) {
    return (
      <div>
        <span className="inspector__label">Citations</span>
        <p className="muted">Select a sentence to view citations.</p>
      </div>
    );
  }

  const factById = new Map(paragraphView.facts.map((fact) => [fact.id, fact]));
  const linkedFacts = paragraphView.links
    .filter((link) => link.sentence_id === activeSentenceId)
    .map((link) => factById.get(link.fact_id))
    .filter(Boolean);

  return (
    <div>
      <span className="inspector__label">Citations</span>
      {linkedFacts.length ? (
        <div className="run-list">
          {linkedFacts.map((fact) => (
            <Card key={fact.id} className="run-card">
              <div className="chip-row">
                <Badge>{fact.source_type}</Badge>
                {fact.span_id ? <Badge variant="muted">Span: {fact.span_id}</Badge> : null}
                {typeof fact.confidence === "number" ? (
                  <Badge variant="muted">Confidence: {fact.confidence}</Badge>
                ) : null}
              </div>
              <p>{fact.content}</p>
              <small className="muted">{fact.id}</small>
            </Card>
          ))}
        </div>
      ) : (
        <p className="muted">No citations linked to this sentence.</p>
      )}
    </div>
  );
}

export default CitationList;

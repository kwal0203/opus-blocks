import Badge from "../../components/ui/Badge";
import Card from "../../components/ui/Card";

function AllowedFactsList({ paragraphView }) {
  if (!paragraphView) {
    return null;
  }

  const allowedIds = paragraphView.paragraph.allowed_fact_ids || [];
  const factById = new Map(paragraphView.facts.map((fact) => [fact.id, fact]));

  return (
    <div>
      <span className="inspector__label">Allowed Facts</span>
      {allowedIds.length ? (
        <div className="run-list">
          {allowedIds.map((factId) => {
            const fact = factById.get(factId);
            return (
              <Card key={factId} className="run-card">
                <div className="chip-row">
                  {fact?.source_type ? <Badge>{fact.source_type}</Badge> : null}
                  {fact?.span_id ? <Badge variant="muted">Span: {fact.span_id}</Badge> : null}
                  {typeof fact?.confidence === "number" ? (
                    <Badge variant="muted">Confidence: {fact.confidence}</Badge>
                  ) : null}
                </div>
                {fact?.content ? <p>{fact.content}</p> : null}
                <small className="muted">{factId}</small>
              </Card>
            );
          })}
        </div>
      ) : (
        <p className="muted">No allowed facts selected yet.</p>
      )}
    </div>
  );
}

export default AllowedFactsList;

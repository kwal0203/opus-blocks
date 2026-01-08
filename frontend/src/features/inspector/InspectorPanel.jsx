import AllowedFactsList from "./AllowedFactsList";
import CitationList from "./CitationList";
import ParagraphInspector from "./ParagraphInspector";
import RunHistory from "./RunHistory";
import SentenceInspector from "./SentenceInspector";

function InspectorPanel({
  paragraphView,
  paragraphRuns,
  paragraphJobStatus,
  activeSentenceId,
  activeSentence,
  isRunsLoading,
  runsError,
  isParagraphLoading
}) {
  return (
    <section className="panel">
      <h2>Inspector</h2>
      {paragraphView ? (
        <div className="inspector">
          <ParagraphInspector
            paragraph={paragraphView.paragraph}
            paragraphJobStatus={paragraphJobStatus}
          />
          <AllowedFactsList
            paragraphView={paragraphView}
            isLoading={isParagraphLoading}
          />
          <SentenceInspector activeSentence={activeSentence} />
          <CitationList
            paragraphView={paragraphView}
            activeSentenceId={activeSentenceId}
            isLoading={isParagraphLoading}
          />
          <RunHistory
            paragraphRuns={paragraphRuns}
            isLoading={isRunsLoading}
            errorMessage={runsError}
          />
        </div>
      ) : (
        <p className="muted">Load a paragraph to inspect details.</p>
      )}
    </section>
  );
}

export default InspectorPanel;

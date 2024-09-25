interface SourcesProps {
  retrieverResults: Array<{
    page_content: string;
    metadata: { url: string };
    score: number;
  }>;
}

const SourcesComponent: React.FC<SourcesProps> = ({ retrieverResults }) => {
  const formatRetrieverResults = (
    results: Array<{
      page_content: string;
      metadata: { url: string };
      score: number;
    }>,
  ) => {
    return results.map((result, index) => (
      <div key={index} className="mb-2">
        <a
          href={result.metadata.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500 underline"
        >
          {result.metadata.url}
        </a>
        <p>{result.page_content.slice(0, 300)}...</p>
      </div>
    ));
  };

  return (
    <div className="flex-1 h-full card">
      <h2 className="text-xl font-semibold">Sources:</h2>
      <div className=" card-body bg-neutral text-neutral-content p-4 mt-2 overflow-auto h-full">
        {retrieverResults.length > 0 ? (
          <div>{formatRetrieverResults(retrieverResults)}</div>
        ) : (
          <p>Pas de source.</p>
        )}
      </div>
    </div>
  );
};

export default SourcesComponent;

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';

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
    }>
  ) => {
    return results.map((result, index) => {
      const [isExpanded, setIsExpanded] = useState(false);

      return (
        <div key={index} className="mb-2">
          {/* Clickable URL link */}
          <a
            href={result.metadata.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 underline"
          >
            {result.metadata.url}
          </a>

          {/* Toggle Button for Collapse/Expand */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="ml-2"
          >
            {isExpanded ? 'Cacher' : 'Montrer'} le resumé de la page
          </button>

          {/* Conditionally Render the Content using ReactMarkdown */}
          {isExpanded ? (
            <div>
              <ReactMarkdown>{result.page_content}</ReactMarkdown>
            </div>
          ) : (
            <div className="h-24 overflow-auto">
              <ReactMarkdown>{result.page_content}</ReactMarkdown>
            </div>
          )}
        </div>
      );
    });
  };

  return (
    <div className="flex-1 h-full card">
      <h2 className="text-xl font-semibold">Sources:</h2>
      <div className="card-body bg-neutral text-neutral-content p-4 mt-2 overflow-auto h-full">
        {retrieverResults.length > 0 ? (
          <div>{formatRetrieverResults(retrieverResults)}</div>
        ) : (
          <p>No sources available.</p>
        )}
      </div>
    </div>
  );
};

export default SourcesComponent;
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm"; // Enables GitHub-flavored markdown, such as links
import rehypeRaw from "rehype-raw"; // Allows raw HTML if you need it (optional)

interface ResponseProps {
  llmResponse: string;
}

const ResponseComponent: React.FC<ResponseProps> = ({ llmResponse }) => {
  return (
    <div className="flex-1 h-full card">
      <h2 className="text-xl font-semibold">Réponse du modèle:</h2>
      <div className="card-body bg-neutral text-neutral-content p-4 mt-2 overflow-auto h-full">
        <ReactMarkdown
          className="whitespace-pre-wrap"
          remarkPlugins={[remarkGfm]} // Enables support for things like links and tables
          rehypePlugins={[rehypeRaw]} // Optional: Only if you have HTML inside your markdown
          components={{
            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 underline"
              >
                {children}
              </a>
            ),
          }}
        >
          {llmResponse}
        </ReactMarkdown>
      </div>
    </div>
  );
};

export default ResponseComponent;
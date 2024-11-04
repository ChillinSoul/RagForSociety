import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm"; // Enables GitHub-flavored markdown, such as links
import rehypeRaw from "rehype-raw"; // Allows raw HTML if you need it (optional)

interface ResponseProps {
  llmResponse: string;
}

const ResponseComponent: React.FC<ResponseProps> = ({ llmResponse }) => {
  return (
    <div className="flex-1 h-full ">
      <div className=" p-4 m-8 bg-base-200 rounded-xl overflow-auto h-full">
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
                tabIndex={0}
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

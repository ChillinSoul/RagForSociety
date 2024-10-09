import ReactMarkdown from "react-markdown";

interface ResponseProps {
  llmResponse: string;
}

const ResponseComponent: React.FC<ResponseProps> = ({ llmResponse }) => {


  return (
    <div className="flex-1 h-full card ">
      <h2 className="text-xl font-semibold">Réponse du modèle:</h2>
      <div className="card-body bg-neutral text-neutral-content p-4 mt-2  overflow-auto h-full">
        <ReactMarkdown className="whitespace-pre-wrap">
          {llmResponse}
        </ReactMarkdown>
      </div>
    </div>
  );
};

export default ResponseComponent;

interface ResponseProps {
  llmResponse: string;
}

const ResponseComponent: React.FC<ResponseProps> = ({ llmResponse }) => {
    const formatLlmResponse = (response: string) => {
        const formattedResponse = response.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
        let resp = formattedResponse.split("\n").map((line, index) => (
          <p key={index} dangerouslySetInnerHTML={{ __html: line }}></p>
        ));
      
        return resp;
      };

  return (
    <div className="flex-1 h-full card ">
      <h2 className="text-xl font-semibold">Réponse du modèle:</h2>
      <div className="card-body bg-neutral text-neutral-content p-4 mt-2  overflow-auto h-full">
        <div className="whitespace-pre-wrap">
          {formatLlmResponse(llmResponse)}
        </div>
      </div>
    </div>
  );
};

export default ResponseComponent;

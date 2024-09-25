"use client";

import React, { useState } from 'react';
import { useMutation, UseMutationResult } from '@tanstack/react-query';

// Define the expected API response structure
interface ApiResponse {
  retriever_results: Array<{
    page_content: string;
    metadata: {
      url: string;
    };
    score: number;
  }>;
  llm_response: string;
}

// Function to fetch the response from the API
const fetchResponse = async (question: string): Promise<ApiResponse> => {
  const res = await fetch('http://127.0.0.1:8000/get-response/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    throw new Error('Failed to fetch response');
  }

  const data: ApiResponse = await res.json(); // Expecting a JSON response
  return data;
};

// Format the retriever results
const formatRetrieverResults = (results: Array<{ page_content: string; metadata: { url: string }; score: number }>) => {
  return results.map((result, index) => (
    <div key={index} className="mb-2">
      <a href={result.metadata.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">
        {result.metadata.url}
      </a>
      <p>{result.page_content.slice(0, 300)}...</p> {/* Show a snippet of the content */}
    </div>
  ));
};

// Format the LLM response
const formatLlmResponse = (response: string) => {
  return response.split('\n').map((line, index) => (
    <p key={index}>{line}</p>
  ));
};

// React component with Tailwind and DaisyUI styling
const QueryComponent: React.FC = () => {
  const [query, setQuery] = useState<string>(''); // Store user input
  const [showResponse, setShowResponse] = useState<boolean>(false); // Control when to display the response

  // Mutation to handle API request using fetchResponse
  const mutation: UseMutationResult<ApiResponse, Error, string> = useMutation({
    mutationFn: fetchResponse, // Pass mutation function here
    onSuccess: () => {
      setShowResponse(true); // Show the response when the mutation is successful
    },
  });

  // Function to handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowResponse(false); // Hide the response until a new one is fetched
    if (query) {
      mutation.mutate(query); // Trigger the mutation with the user query
    }
  };

  return (
    <div className="p-8 min-h-screen flex justify-center items-center">
      <div className="card w-full bg-base-100">
        <div className="card-body">
          <h1 className="text-2xl font-bold mb-4">Posez-moi une question</h1>
          <form onSubmit={handleSubmit}>
            <div className="form-control">
              <label htmlFor="query" className="label">
                <span className="label-text">Votre question:</span>
              </label>
              <input
                type="text"
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Votre question"
                required
                className="input input-secondary w-full"
              />
            </div>

            <button type="submit" className="btn btn-secondary mt-4" disabled={mutation.isPending}>
              Valider
            </button>
          </form>

          {/* Loading, error, and success states */}
          {mutation.isPending && (
            <div className="alert alert-info mt-4">Génération de la reponse...</div>
          )}

          {mutation.isError && (
            <div className="alert alert-error mt-4">
              <span>Error: {mutation.error?.message || 'Oops il y a eu une erreur'}</span>
            </div>
          )}

          {mutation.isSuccess && showResponse && mutation.data && (
            <div className="mt-6 flex flex-row-reverse gap-4">
              <div className="flex-1 ">
                <h2 className="text-xl font-semibold">Sources:</h2>
                <div className="bg-neutral text-neutral-content p-4 mt-2 rounded-lg overflow-auto h-96">
                  {mutation.data.retriever_results.length > 0 ? (
                    <div>{formatRetrieverResults(mutation.data.retriever_results)}</div>
                  ) : (
                    <p>Pas de source.</p>
                  )}
                </div>
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold">Réponse du modèle:</h2>
                <div className="bg-neutral text-neutral-content p-4 mt-2 rounded-lg overflow-auto h-96">
                  <div className="whitespace-pre-wrap">
                    {formatLlmResponse(mutation.data.llm_response)}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QueryComponent;
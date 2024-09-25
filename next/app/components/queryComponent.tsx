"use client";

import React, { useState } from "react";
import { useMutation, UseMutationResult } from "@tanstack/react-query";
import SourcesComponent from "./sourcesComponent";
import ResponseComponent from "./responseComponent";
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
  const res = await fetch("http://127.0.0.1:8000/get-response/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    throw new Error("Failed to fetch response");
  }

  const data: ApiResponse = await res.json(); // Expecting a JSON response
  return data;
};

// React component with Tailwind and DaisyUI styling
const QueryComponent: React.FC = () => {
  const [query, setQuery] = useState<string>("");
  const [showResponse, setShowResponse] = useState<boolean>(false);

  const mutation: UseMutationResult<ApiResponse, Error, string> = useMutation({
    mutationFn: fetchResponse,
    onSuccess: () => {
      setShowResponse(true);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowResponse(false);
    if (query) {
      mutation.mutate(query);
    }
  };

  return (
    <div className="p-8 py-20 h-screen gap-4 grid grid-cols-3 grid-rows-3">
      <section className="col-span-2">
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

          <button
            type="submit"
            className="btn btn-secondary mt-4"
            disabled={mutation.isPending}
          >
            Valider
          </button>
        </form>

        {mutation.isPending && <progress className="progress"></progress>}

        {mutation.isError && (
          <div className="alert alert-error mt-4">
            <span>
              Error: {mutation.error?.message || "Oops il y a eu une erreur"}
            </span>
          </div>
        )}
      </section>

      {mutation.isSuccess && showResponse && mutation.data ? (
        <>
          <section className="col-span-1 row-span-3 h-full">
            <SourcesComponent
              retrieverResults={mutation.data.retriever_results}
            />
          </section>
          <section className="col-span-2 row-span-2 h-full">
            <ResponseComponent llmResponse={mutation.data.llm_response} />
          </section>
        </>
      ):mutation.isPending ? (
        <>
            <section className="col-span-1 row-span-3 h-full opacity-10 ">
                <SourcesComponent retrieverResults={[]} />
            </section>
            <section className="col-span-2 row-span-2 h-full opacity-10">
                <ResponseComponent llmResponse={""} />
            </section>
        </>
      ):null}
    </div>
  );
};

export default QueryComponent;

"use client";

import React, { useState } from "react";
import { useMutation, UseMutationResult } from "@tanstack/react-query";
import SourcesComponent from "./sourcesComponent";
import ResponseComponent from "./responseComponent";
import McqComponent from "./mcqComponent";

interface ApiResponse {
  retriever_results: Array<{
    page_content: string;
    metadata: {
      url: string;
    };
    score: number;
  }>;
  llm_response: string;

  mc_response: {
    questions: Array<{
      text: string;
      options: string[];
    }>;
  };
}

interface qnr {
  question: string;
  reponse: string;
}

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

  const data: ApiResponse = await res.json();
  return data;
};

const fetchResponseBNF = async (question: string, questionaire: Array<qnr>): Promise<ApiResponse> => {
  const res = await fetch("http://127.0.0.1:8000/get-response-bnf/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question, questionaire }),
  });

  if (!res.ok) {
    throw new Error("Failed to fetch response");
  }

  const data: ApiResponse = await res.json();
  return data;
};

const QueryComponent: React.FC = () => {
  const [query, setQuery] = useState<string>("");
  const [showResponse, setShowResponse] = useState<boolean>(false);
  const [showMcq, setShowMcq] = useState<boolean>(false);
  const [questionaireAnswered, setQuestionaireAnswered] = useState<boolean>(false);

  // First mutation (Initial question submission)
  const responseMutation: UseMutationResult<ApiResponse, Error, string> = useMutation({
    mutationFn: fetchResponse,
    onSuccess: () => {
      setShowResponse(true);
      setShowMcq(false);
    },
  });

  // Second mutation (MCQ submission)
  const responseBNFMutation: UseMutationResult<ApiResponse, Error, { question: string; questionaire: Array<qnr> }> = useMutation({
    mutationFn: ({ question, questionaire }) => fetchResponseBNF(question, questionaire),
    onSuccess: () => {
      setShowResponse(true);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowResponse(false);
    if (query) {
      // Reset responseBNFMutation whenever a new query is submitted
      responseBNFMutation.reset();
      responseMutation.mutate(query);
      setQuestionaireAnswered(false);
    }
  };

  const handleMCQSubmit = (questionaire: Array<qnr>) => {
    setShowResponse(false);
    if (query) {
      responseBNFMutation.mutate({ question: query, questionaire });
      setShowMcq(false);
      setQuestionaireAnswered(true);
    }
  };

  return (
    <div className="p-8 pt-20 h-screen gap-4 grid grid-cols-3 grid-rows-9">
      <section className="col-span-2 row-span-2">
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
            disabled={responseMutation.isPending || responseBNFMutation.isPending}
          >
            Valider
          </button>
        </form>

        {(responseMutation.isPending|| responseBNFMutation.isPending )&& <progress className="progress"></progress>}

        {responseMutation.isError && (
          <div className="alert alert-error mt-4">
            <span>
              Error: {responseMutation.error?.message || "Oops il y a eu une erreur"}
            </span>
          </div>
        )}
      </section>

      {(responseMutation.isSuccess || responseBNFMutation.isSuccess) && showResponse && (
        <>
          <section className="col-span-1 row-span-9 h-full">
            <SourcesComponent
              retrieverResults={
                responseBNFMutation.isSuccess
                  ? responseBNFMutation.data?.retriever_results || []
                  : responseMutation.data?.retriever_results || []
              }
            />
          </section>
          {!questionaireAnswered && (
            <button className="btn btn-primary col-span-2 row-span-1" onClick={() => setShowMcq(!showMcq)}>
              {showMcq ? "Afficher la réponse" : "Améliorer la réponse avec des questions"}
            </button>
          )}
          <section className="col-span-2 row-span-6 h-full">
            {showMcq ? (
              <McqComponent
                questions={
                  responseBNFMutation.isSuccess
                    ? responseBNFMutation.data?.mc_response.questions || []
                    : responseMutation.data?.mc_response.questions || []
                }
                onSubmit={handleMCQSubmit}
              />
            ) : (
              <ResponseComponent
                llmResponse={
                  responseBNFMutation.isSuccess
                    ? responseBNFMutation.data?.llm_response || ""
                    : responseMutation.data?.llm_response || ""
                }
              />
            )}
          </section>
        </>
      )}
    </div>
  );
};

export default QueryComponent;
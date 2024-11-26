"use client";

import React, { useState } from "react";
import { useMutation, UseMutationResult } from "@tanstack/react-query";
import SourcesComponent from "./sourcesComponent";
import ResponseComponent from "./responseComponent";
import McqComponent from "./mcqComponent";
import QueryBar from "./queryBar";
import TokenCounter from "./TokenCounter";
import { useAutoAnimate } from "@formkit/auto-animate/react";

interface TokenCounts {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

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
  token_counts: TokenCounts;
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

const fetchResponseBNF = async (
  question: string,
  questionaire: Array<qnr>
): Promise<ApiResponse> => {
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

const Home = () => {
  const [query, setQuery] = useState<string>("");
  const [showResponse, setShowResponse] = useState<boolean>(false);
  const [showMcq, setShowMcq] = useState<boolean>(false);
  const [questionaireAnswered, setQuestionaireAnswered] = useState<boolean>(
    false
  );
  const [tokenCounts, setTokenCounts] = useState<TokenCounts>({
    prompt_tokens: 0,
    completion_tokens: 0,
    total_tokens: 0,
  });

  const [parent, enableAnimations] = useAutoAnimate();

  const responseMutation: UseMutationResult<
    ApiResponse,
    Error,
    string
  > = useMutation({
    mutationFn: fetchResponse,
    onSuccess: (data) => {
      console.log("Response received:", data);
      console.log("Token counts:", data.token_counts);
      setShowResponse(true);
      setShowMcq(false);
      setTokenCounts((prevCounts) => {
        const newCounts = {
          prompt_tokens:
            prevCounts.prompt_tokens + data.token_counts.prompt_tokens,
          completion_tokens:
            prevCounts.completion_tokens + data.token_counts.completion_tokens,
          total_tokens:
            prevCounts.total_tokens + data.token_counts.total_tokens,
        };
        console.log("Updated token counts:", newCounts);
        return newCounts;
      });
    },
  });

  const responseBNFMutation: UseMutationResult<
    ApiResponse,
    Error,
    { question: string; questionaire: Array<qnr> }
  > = useMutation({
    mutationFn: ({ question, questionaire }) =>
      fetchResponseBNF(question, questionaire),
    onSuccess: (data) => {
      console.log("BNF Response received:", data);
      console.log("BNF Token counts:", data.token_counts);
      setShowResponse(true);
      setTokenCounts((prevCounts) => {
        const newCounts = {
          prompt_tokens:
            prevCounts.prompt_tokens + data.token_counts.prompt_tokens,
          completion_tokens:
            prevCounts.completion_tokens + data.token_counts.completion_tokens,
          total_tokens:
            prevCounts.total_tokens + data.token_counts.total_tokens,
        };
        console.log("Updated BNF token counts:", newCounts);
        return newCounts;
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowResponse(false);
    if (query) {
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

  const isPending = responseMutation.isPending || responseBNFMutation.isPending;

  return (
    <div className="w-full h-full relative">
      <ul className="flex flex-row h-[calc(100%-190px)]" ref={parent}>
        {(responseMutation.isSuccess || responseBNFMutation.isSuccess) &&
          showResponse && (
            <>
              <li className="h-full w-96" key="sources">
                <SourcesComponent
                  retrieverResults={
                    responseBNFMutation.isSuccess
                      ? responseBNFMutation.data?.retriever_results || []
                      : responseMutation.data?.retriever_results || []
                  }
                />
              </li>
            </>
          )}
        {(responseMutation.isSuccess || responseBNFMutation.isSuccess) &&
          showResponse && (
            <>
              {showMcq ? (
                <li className="h-full w-[calc(100%-384px)]" key="mcq">
                  <McqComponent
                    questions={
                      responseBNFMutation.isSuccess
                        ? responseBNFMutation.data?.mc_response.questions || []
                        : responseMutation.data?.mc_response.questions || []
                    }
                    onSubmit={handleMCQSubmit}
                  />
                </li>
              ) : (
                <li className="h-full w-[calc(100%-384px)]" key="response">
                  <ResponseComponent
                    llmResponse={
                      responseBNFMutation.isSuccess
                        ? responseBNFMutation.data?.llm_response || ""
                        : responseMutation.data?.llm_response || ""
                    }
                  />
                </li>
              )}
            </>
          )}
      </ul>

      <div className="absolute bottom-24 w-full z-50">
        {(responseMutation.isSuccess || responseBNFMutation.isSuccess) &&
          showResponse &&
          !questionaireAnswered && (
            <button
              className="btn ml-8"
              onClick={() => setShowMcq(!showMcq)}
              tabIndex={0}
            >
              {showMcq
                ? "Afficher la réponse"
                : "Améliorer la réponse avec des questions"}
            </button>
          )}
      </div>

      <TokenCounter
        promptTokens={tokenCounts.prompt_tokens}
        completionTokens={tokenCounts.completion_tokens}
        isPending={isPending}
      />

      {isPending && (
        <div className="mx-8">
          <progress className="progress"></progress>
        </div>
      )}

      <QueryBar
        query={query}
        setQuery={setQuery}
        handleSubmit={handleSubmit}
        responseMutation={responseMutation}
        responseBNFMutation={responseBNFMutation}
      />
    </div>
  );
};

export default Home;

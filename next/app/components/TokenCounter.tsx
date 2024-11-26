import React from "react";
import { Loader2 } from "lucide-react";

const TokenCounter = ({
  promptTokens = 0,
  completionTokens = 0,
  isPending = false,
}) => {
  const totalTokens = promptTokens + completionTokens;
  const tokenLimit = 16000; // Example limit
  const usagePercentage = (totalTokens / tokenLimit) * 100;

  return (
    <div className="fixed bottom-24 right-8 bg-base-200 p-4 rounded-lg shadow-lg z-50">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm font-medium">Prompt Tokens:</span>
          <span className="font-mono">{promptTokens.toLocaleString()}</span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm font-medium">Completion Tokens:</span>
          <span className="font-mono">{completionTokens.toLocaleString()}</span>
        </div>
        <div className="border-t border-gray-200 my-2"></div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm font-medium">Total Tokens:</span>
          <span className="font-mono">{totalTokens.toLocaleString()}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-secondary h-2.5 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(usagePercentage, 100)}%` }}
          ></div>
        </div>
        {isPending && (
          <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
            <Loader2 className="animate-spin h-4 w-4" />
            <span>Processing...</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default TokenCounter;

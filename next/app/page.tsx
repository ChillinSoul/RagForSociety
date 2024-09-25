"use client";

import QueryComponent from "./components/queryComponent";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

export default function Home() {
  return (

    <QueryClientProvider client={queryClient}>
    <QueryComponent />
    </QueryClientProvider>
  );
}

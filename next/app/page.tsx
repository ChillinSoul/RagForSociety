"use client";

import HomeComponent from "./components/home";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

export default function Home() {
  return (
    <QueryClientProvider client={queryClient}>
      <HomeComponent />
    </QueryClientProvider>
  );
}

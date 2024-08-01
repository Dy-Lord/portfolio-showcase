import { BrowserRouter, Route, Routes } from "react-router-dom";
import { BasicLayout } from "./layouts/BasicLayout";
import { LandingPage } from "./pages/LandingPage/LandingPage";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 600 * 1000,
    },
  },
});

export const App = () => {
  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <Routes>
          <Route path="/" element={<BasicLayout />}>
            <Route index element={<LandingPage />} />
          </Route>
        </Routes>
      </QueryClientProvider>
    </BrowserRouter>
  );
}

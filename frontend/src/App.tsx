import "@mantine/core/styles.css";
import "@mantine/charts/styles.css";
import "@mantine/notifications/styles.css";
import "./App.css";
import { MantineProvider, ColorSchemeScript } from "@mantine/core";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Notifications } from "@mantine/notifications";
import { BrowserRouter } from "react-router-dom";
import { theme } from "./theme";
import AppRoutes from "./routes";
import ErrorBoundary from "./components/ErrorBoundary/ErrorBoundary";

// Create Query Client with enhanced error handling
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error && "status" in error && typeof error.status === "number") {
          return error.status >= 500 && failureCount < 2;
        }
        return failureCount < 1;
      },
      staleTime: 5000,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: false,
    },
  },
});

function App() {
  return (
    <>
      <ColorSchemeScript defaultColorScheme="auto" />
      <MantineProvider theme={theme} defaultColorScheme="auto">
        <Notifications position="top-right" limit={5} autoClose={4000} />
        <ErrorBoundary>
          <QueryClientProvider client={queryClient}>
            <BrowserRouter>
              <AppRoutes />
            </BrowserRouter>
          </QueryClientProvider>
        </ErrorBoundary>
      </MantineProvider>
    </>
  );
}

export default App;

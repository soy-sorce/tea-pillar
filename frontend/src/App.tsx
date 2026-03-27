// src/App.tsx
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { GenerationContextProvider } from "@/contexts/GenerationContext";
import { AppLayout } from "@/components/layout/AppLayout";
import { LandingPage } from "@/pages/LandingPage";
import { ExperiencePage } from "@/pages/ExperiencePage";
import { ProductionPage } from "@/pages/ProductionPage";
import { ResultPage } from "@/pages/ResultPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: "experience", element: <ExperiencePage /> },
      { path: "production", element: <ProductionPage /> },
      { path: "result", element: <ResultPage /> },
    ],
  },
]);

export function App(): React.JSX.Element {
  return (
    <GenerationContextProvider>
      <RouterProvider router={router} />
    </GenerationContextProvider>
  );
}

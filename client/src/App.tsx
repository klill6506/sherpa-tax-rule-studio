import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import FormEditor from "./pages/FormEditor";
import SourceLibrary from "./pages/SourceLibrary";

function WelcomePage() {
  return (
    <div className="flex h-full items-center justify-center text-gray-400">
      <div className="text-center">
        <h2 className="text-2xl font-semibold mb-2">Sherpa Tax Rule Studio</h2>
        <p>Select a form from the sidebar or create a new one.</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<WelcomePage />} />
        <Route path="forms/:formId" element={<FormEditor />} />
        <Route path="sources" element={<SourceLibrary />} />
      </Route>
    </Routes>
  );
}

import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { PROJECT_NAME } from "../config";

// Set the document title and OpenGraph description dynamically from config
try {
	if (typeof document !== 'undefined') {
		document.title = PROJECT_NAME;
		const ogDesc = document.querySelector('meta[property="og:description"]');
		if (ogDesc) ogDesc.setAttribute('content', `${PROJECT_NAME} for Samsung Prism`);
		const ogTitle = document.querySelector('meta[property="og:title"]');
		if (ogTitle) ogTitle.setAttribute('content', PROJECT_NAME);
	}
} catch (e) {
	// ignore in non-browser environments
}

createRoot(document.getElementById("root")!).render(<App />);

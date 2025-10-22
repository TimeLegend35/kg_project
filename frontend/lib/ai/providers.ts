/**
 * BGB Chat Provider - Nutzt FastAPI + LangGraph Backend
 * Ersetzt Vercel AI Gateway mit direkten Backend-Calls
 */
import { bgbProvider } from './bgb-provider';
import { isTestEnvironment } from "../constants";

// Für Tests nutzen wir Mock Models, sonst unser FastAPI Backend
export const myProvider = isTestEnvironment
  ? (() => {
      const {
        artifactModel,
        chatModel,
        reasoningModel,
        titleModel,
      } = require("./models.mock");
      return {
        languageModel: (modelId: string) => {
          // Map zu entsprechenden Mock Models
          if (modelId.includes('reasoning')) return reasoningModel;
          if (modelId.includes('title')) return titleModel;
          if (modelId.includes('artifact')) return artifactModel;
          return chatModel;
        }
      };
    })()
  : bgbProvider;

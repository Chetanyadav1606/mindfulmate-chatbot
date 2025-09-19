import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardHeader, CardContent } from "./components/ui/card";
import { ScrollArea } from "./components/ui/scroll-area";
import { Separator } from "./components/ui/separator";
import { Send, Heart, Brain, Sparkles } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Typing indicator component
const TypingIndicator = () => {
  return (
    <div className="flex items-center space-x-1 p-3">
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"></div>
        <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
        <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
      </div>
      <span className="text-sm text-emerald-600 ml-2">MindfulMate is typing...</span>
    </div>
  );
};

// Message component
const Message = ({ message, isUser, timestamp }) => {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-xs lg:max-w-md xl:max-w-lg ${
        isUser 
          ? 'bg-gradient-to-r from-blue-400 to-indigo-500 text-white' 
          : 'bg-white border border-emerald-200 text-gray-800'
      } rounded-2xl px-4 py-3 shadow-sm`}>
        {!isUser && (
          <div className="flex items-center mb-2">
            <Brain className="w-4 h-4 text-emerald-600 mr-1" />
            <span className="text-xs font-medium text-emerald-600">MindfulMate</span>
          </div>
        )}
        <p className="text-sm whitespace-pre-wrap">{message}</p>
        <p className={`text-xs mt-1 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
        </p>
      </div>
    </div>
  );
};

// Quick suggestion buttons
const QuickSuggestions = ({ onSuggestion, disabled }) => {
  const suggestions = [
    "How are you feeling today?",
    "I'd like to try a breathing exercise",
    "Can you help me with stress?",
    "I need some encouragement"
  ];

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {suggestions.map((suggestion, index) => (
        <Button
          key={index}
          variant="outline"
          size="sm"
          className="text-xs rounded-full border-emerald-200 text-emerald-700 hover:bg-emerald-50"
          onClick={() => onSuggestion(suggestion)}
          disabled={disabled}
        >
          {suggestion}
        </Button>
      ))}
    </div>
  );
};

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Welcome message
  useEffect(() => {
    const welcomeMessage = {
      id: 'welcome',
      message: "Hello! I'm MindfulMate, your mental wellness companion. 🌱 I'm here to support you through life's ups and downs. How are you feeling today?",
      sender: 'assistant',
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
  }, []);

  const sendMessage = async (messageText = inputMessage) => {
    if (!messageText.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      message: messageText,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);
    setIsTyping(true);

    try {
      // Add realistic delay for typing animation
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const response = await axios.post(`${API}/chat`, {
        message: messageText,
        session_id: sessionId
      });

      setIsTyping(false);

      const aiMessage = {
        id: Date.now().toString() + '_ai',
        message: response.data.message,
        sender: 'assistant',
        timestamp: response.data.timestamp
      };

      setMessages(prev => [...prev, aiMessage]);
      setSessionId(response.data.session_id);

    } catch (error) {
      console.error('Chat error:', error);
      setIsTyping(false);
      
      const errorMessage = {
        id: Date.now().toString() + '_error',
        message: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
        sender: 'assistant',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  const handleSuggestion = (suggestion) => {
    sendMessage(suggestion);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-gradient-to-r from-emerald-400 to-teal-500 p-3 rounded-full">
              <Brain className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">MindfulMate</h1>
          <p className="text-lg text-gray-600">Your AI Mental Wellness Companion</p>
          <div className="flex items-center justify-center mt-4 space-x-4">
            <div className="flex items-center text-emerald-600">
              <Heart className="w-4 h-4 mr-1" />
              <span className="text-sm">Empathetic</span>
            </div>
            <div className="flex items-center text-teal-600">
              <Sparkles className="w-4 h-4 mr-1" />
              <span className="text-sm">Supportive</span>
            </div>
            <div className="flex items-center text-cyan-600">
              <Brain className="w-4 h-4 mr-1" />
              <span className="text-sm">Understanding</span>
            </div>
          </div>
        </div>

        {/* Chat Container */}
        <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-t-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                <span className="font-medium">Chat Session Active</span>
              </div>
              <span className="text-sm opacity-90">Safe & Confidential</span>
            </div>
          </CardHeader>
          
          <CardContent className="p-0">
            {/* Messages Area */}
            <ScrollArea className="h-96 p-6">
              <div className="space-y-4">
                {messages.map((msg) => (
                  <Message
                    key={msg.id}
                    message={msg.message}
                    isUser={msg.sender === 'user'}
                    timestamp={msg.timestamp}
                  />
                ))}
                {isTyping && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <Separator />

            {/* Quick Suggestions */}
            <div className="p-4">
              <p className="text-sm text-gray-600 mb-3">Try asking about:</p>
              <QuickSuggestions 
                onSuggestion={handleSuggestion} 
                disabled={isLoading}
              />
            </div>

            <Separator />

            {/* Input Area */}
            <div className="p-6">
              <form onSubmit={handleSubmit} className="flex gap-3">
                <Input
                  type="text"
                  placeholder="Share what's on your mind..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  disabled={isLoading}
                  className="flex-1 border-emerald-200 focus:border-emerald-400 focus:ring-emerald-400"
                />
                <Button
                  type="submit"
                  disabled={isLoading || !inputMessage.trim()}
                  className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white px-6"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </form>
              <p className="text-xs text-gray-500 mt-2 text-center">
                Remember: This is not a substitute for professional mental health care.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-gray-500">
          <p>Your privacy matters. Conversations are confidential and secure.</p>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ChatInterface />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
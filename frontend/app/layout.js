import "./globals.css";

export const metadata = {
  title: "The Lenny Growth Assistant",
  description: "AI-powered product management and growth conversational intelligence platform grounded in Lenny Rachitsky's podcast transcripts."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body>{children}</body>
    </html>
  );
}

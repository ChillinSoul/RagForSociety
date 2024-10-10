import type { Metadata } from "next";
import "./globals.css";
import Navbar from "./components/navbar";
import { Roboto_Mono } from "next/font/google";

//👇 Configure the object for our second font
const robotoMono = Roboto_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-roboto-mono",
});

export const metadata: Metadata = {
  title: "RAG For Society",
  description: "Generated by create next app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" data-theme="cupkake">
      <body className={`${robotoMono.variable} antialiased bg-neutral `}>
        <div className = "flex flex-row h-screen w-screen">
        <Navbar />
        <div className = "m-8 ml-64 w-full h-auto rounded-xl  bg-base-100">
          {children}
        </div>
        </div>
      </body>
    </html>
  );
}

export {};

declare global {
  interface Window {
    __advantagescoutUnmount?: () => void;
  }
}

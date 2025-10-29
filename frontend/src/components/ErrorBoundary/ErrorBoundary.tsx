import React from 'react';
import { Alert, Button, Stack, Text, Title, Center, Container } from '@mantine/core';
import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; retry: () => void }>;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error!} retry={this.handleRetry} />;
      }

      return (
        <Container size="sm" py="xl">
          <Center>
            <Stack align="center" gap="lg">
              <IconAlertTriangle size={64} color="var(--mantine-color-red-6)" />
              
              <Stack align="center" gap="sm">
                <Title order={2} ta="center">Something went wrong</Title>
                <Text c="dimmed" ta="center" size="sm">
                  An unexpected error occurred in the application. This might be a temporary issue.
                </Text>
              </Stack>

              <Alert
                icon={<IconAlertTriangle size={16} />}
                title="Error Details"
                color="red"
                variant="light"
                maw={600}
              >
                <Text size="sm" c="red.7">
                  {this.state.error?.message || 'Unknown error occurred'}
                </Text>
                
                {import.meta.env.DEV && this.state.error?.stack && (
                  <Text
                    size="xs"
                    c="red.6"
                    mt="sm"
                    style={{
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-all',
                    }}
                  >
                    {this.state.error.stack}
                  </Text>
                )}
              </Alert>

              <Stack gap="sm">
                <Button
                  onClick={this.handleRetry}
                  leftSection={<IconRefresh size={16} />}
                  variant="filled"
                >
                  Try Again
                </Button>
                
                <Button
                  onClick={() => window.location.reload()}
                  variant="light"
                  size="sm"
                >
                  Refresh Page
                </Button>
              </Stack>

              <Text size="xs" c="dimmed" ta="center">
                If this problem persists, please check the console for more details or contact support.
              </Text>
            </Stack>
          </Center>
        </Container>
      );
    }

    return this.props.children;
  }
}

// Simple error fallback component
export function SimpleErrorFallback({ error, retry }: { error: Error; retry: () => void }) {
  return (
    <Alert
      icon={<IconAlertTriangle size={16} />}
      title="Error"
      color="red"
      withCloseButton
      onClose={retry}
    >
      <Stack gap="sm">
        <Text size="sm">{error.message}</Text>
        <Button size="xs" variant="light" onClick={retry} leftSection={<IconRefresh size={14} />}>
          Retry
        </Button>
      </Stack>
    </Alert>
  );
}

export default ErrorBoundary;
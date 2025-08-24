import { useState } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Badge,
  List,
  ListItem,
  Separator,
  Code,
  Grid,
  GridItem
} from '@chakra-ui/react'
import traceData from './assets/trace.json'

interface TraceItem {
  func: string
  impl: string
  rules: any[]
  args: string[]
  kwargs: Record<string, any>
  choice_kwargs: Record<string, any>
  items: TraceItem[]
}

interface RegistryEntry {
  interface: string
  funcs: string[]
  rules: string[]
}

interface TraceData {
  items: TraceItem[]
  registry: Record<string, RegistryEntry>
}

function App() {
  const [data] = useState<TraceData>(traceData as TraceData)

  const renderTraceItem = (item: TraceItem, depth: number = 0) => {
    return (
      <Box key={`${item.func}-${depth}`} ml={depth * 4} mb={4}>
        <Box
          borderWidth="1px"
          borderRadius="md"
          p={4}
          bg="white"
          shadow="sm"
        >
          <VStack align="start" gap={2}>
            <HStack>
              <Badge colorScheme="blue">Function</Badge>
              <Text fontWeight="bold">{item.func}</Text>
            </HStack>
            
            <HStack>
              <Text fontWeight="semibold">Implementation:</Text>
              <Code>{item.impl}</Code>
            </HStack>
            
            <HStack>
              <Text fontWeight="semibold">Args:</Text>
              <Code>[{item.args.join(', ')}]</Code>
            </HStack>
            
            {item.rules.length > 0 && (
              <HStack>
                <Text fontWeight="semibold">Rules:</Text>
                <Code>[{JSON.stringify(item.rules)}]</Code>
              </HStack>
            )}
            
            {Object.keys(item.kwargs).length > 0 && (
              <HStack>
                <Text fontWeight="semibold">Kwargs:</Text>
                <Code>{JSON.stringify(item.kwargs)}</Code>
              </HStack>
            )}
            
            {Object.keys(item.choice_kwargs).length > 0 && (
              <HStack>
                <Text fontWeight="semibold">Choice Kwargs:</Text>
                <Code>{JSON.stringify(item.choice_kwargs)}</Code>
              </HStack>
            )}
            
            {item.items.length > 0 && (
              <Box w="100%">
                <Text fontWeight="semibold" mb={2}>Nested Items:</Text>
                <VStack gap={2} align="stretch">
                  {item.items.map((nestedItem, index) => 
                    renderTraceItem(nestedItem, depth + 1)
                  )}
                </VStack>
              </Box>
            )}
          </VStack>
        </Box>
      </Box>
    )
  }

  return (
    <Box minH="100vh" bg="gray.50">
      <Box bg="white" shadow="sm" borderBottom="1px" borderColor="gray.200">
        <Container maxW="container.xl" py={6}>
          <Heading as="h1" size="xl" color="blue.600">
            PyChoice Trace Viewer
          </Heading>
        </Container>
      </Box>
      
      <Container maxW="container.xl" py={8}>
        <VStack gap={12} align="stretch">
          <Box>
            <Heading as="h2" size="lg" mb={6} color="gray.700">
              Trace Items
            </Heading>
            <VStack gap={4} align="stretch">
              {data.items.length > 0 ? (
                data.items.map((item, index) => renderTraceItem(item))
              ) : (
                <Box
                  borderWidth="1px"
                  borderRadius="md"
                  p={4}
                  bg="white"
                  shadow="sm"
                >
                  <Text color="gray.500">No trace items found.</Text>
                </Box>
              )}
            </VStack>
          </Box>

          <Separator />

          <Box>
            <Heading as="h2" size="lg" mb={6} color="gray.700">
              Registry
            </Heading>
            <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" }} gap={6}>
              {Object.entries(data.registry).map(([key, entry]) => (
                <GridItem key={key}>
                  <Box
                    borderWidth="1px"
                    borderRadius="md"
                    p={4}
                    bg="white"
                    shadow="sm"
                    h="100%"
                  >
                    <VStack align="start" gap={3}>
                      <Heading as="h3" size="md" color="blue.600">
                        {key}
                      </Heading>
                      
                      <HStack>
                        <Text fontWeight="semibold">Interface:</Text>
                        <Code>{entry.interface}</Code>
                      </HStack>
                      
                      <HStack>
                        <Text fontWeight="semibold">Functions:</Text>
                        <Code>[{entry.funcs.join(', ')}]</Code>
                      </HStack>
                      
                      <Box>
                        <Text fontWeight="semibold" mb={2}>Rules:</Text>
                        <List.Root>
                          {entry.rules.map((rule, index) => (
                            <ListItem key={index}>
                              <Code fontSize="sm">{rule}</Code>
                            </ListItem>
                          ))}
                        </List.Root>
                      </Box>
                    </VStack>
                  </Box>
                </GridItem>
              ))}
            </Grid>
          </Box>
        </VStack>
      </Container>
    </Box>
  )
}

export default App

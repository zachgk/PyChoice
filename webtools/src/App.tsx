import { useState } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  Tabs
} from '@chakra-ui/react'
import type { TraceData, TraceItemData } from './components/data';
import traceData from './assets/trace.json'
import Registry from './components/registry'
import TraceItem from './components/trace';


function App() {
  const [data] = useState<TraceData>(traceData as TraceData)


  const renderTraceItems = () => (
    <VStack gap={4} align="stretch">
      {data.items.length > 0 ? (
        data.items.map((item: TraceItemData, index: number) => <TraceItem item={item} depth={0} key={index} />)
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
  )


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
        <Tabs.Root defaultValue="traces" variant="enclosed">
          <Tabs.List>
            <Tabs.Trigger value="traces">
              <Text fontWeight="semibold">Trace Items</Text>
            </Tabs.Trigger>
            <Tabs.Trigger value="registry">
              <Text fontWeight="semibold">Registry</Text>
            </Tabs.Trigger>
          </Tabs.List>
          
          <Tabs.Content value="traces" pt={6}>
            {renderTraceItems()}
          </Tabs.Content>
          
          <Tabs.Content value="registry" pt={6}>
            <Registry registry={data.registry} />
          </Tabs.Content>
        </Tabs.Root>
      </Container>
    </Box>
  )
}

export default App

import { useState } from 'react'
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Heading,
  Text,
  Tabs
} from '@chakra-ui/react'
import type { TraceData } from './components/data';
import traceData from './assets/trace.json'
import Registry from './components/registry'
import TraceItems from './components/trace';


function App() {
  const [data] = useState<TraceData>(traceData as TraceData)
  const location = useLocation()
  const navigate = useNavigate()

  // Extract highlighted registry entry from URL params
  const searchParams = new URLSearchParams(location.search)
  const highlightedEntryId = searchParams.get('highlight')

  // Determine current tab based on route
  const currentTab = location.pathname === '/registry' ? 'registry' : 'traces'

  const handleTabChange = (details: any) => {
    if (details.value === 'registry') {
      navigate('/registry')
    } else {
      navigate('/')
    }
  }

  const navigateToRegistryEntry = (entryId: string) => {
    navigate(`/registry?highlight=${entryId}`)
  }

  const renderTraceItems = () => (
    <Box>
      {data.items.length > 0 ? (
        <TraceItems
          items={data.items}
          registry={data.registry}
          onNavigateToRegistry={navigateToRegistryEntry}
        />
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
    </Box>
  )

  const renderRegistry = () => (
    <Registry
      registry={data.registry}
      highlightedEntryId={highlightedEntryId}
      onClearHighlight={() => navigate('/registry')}
    />
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
        <Tabs.Root value={currentTab} onValueChange={handleTabChange} variant="enclosed">
          <Tabs.List>
            <Tabs.Trigger value="traces">
              <Text fontWeight="semibold">Trace Items</Text>
            </Tabs.Trigger>
            <Tabs.Trigger value="registry">
              <Text fontWeight="semibold">Registry</Text>
            </Tabs.Trigger>
          </Tabs.List>

          <Box pt={6}>
            <Routes>
              <Route path="/" element={renderTraceItems()} />
              <Route path="/registry" element={renderRegistry()} />
            </Routes>
          </Box>
        </Tabs.Root>
      </Container>
    </Box>
  )
}

export default App

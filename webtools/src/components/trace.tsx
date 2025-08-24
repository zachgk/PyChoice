import {
  Box,
  Text,
  VStack,
  HStack,
  Badge,
  Code,
} from '@chakra-ui/react'
import type { TraceItemData } from './data';

interface TraceItemProps {
    item: TraceItemData;
    depth: number;
}

function TraceItem(props: TraceItemProps) {
    const {item, depth} = props;
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
                  {item.items.map((nestedItem: TraceItemData, index: number) => 
                    <TraceItem item={nestedItem} depth={depth + 1} key={index} />
                  )}
                </VStack>
              </Box>
            )}
          </VStack>
        </Box>
      </Box>
    );
}  

export default TraceItem
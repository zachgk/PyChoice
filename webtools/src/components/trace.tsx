import {
  Box,
  Text,
  VStack,
  HStack,
  Badge,
  Code,
  TreeView,
  createTreeCollection,
  Grid,
  GridItem,
  Heading
} from '@chakra-ui/react'
import { LuChevronRight } from "react-icons/lu"
import { useState } from 'react'
import type { TraceItemData, ChoiceFunction } from './data';
import { findImplementationName } from './utils';

interface TraceItemsProps {
    items: TraceItemData[];
    registry: Record<string, ChoiceFunction>;
    onNavigateToRegistry?: (entryId: string) => void;
}

interface TreeNode {
  id: string;
  name: string;
  data: TraceItemData;
  children?: TreeNode[];
}

function TraceDetails(props: { traceItem: TraceItemData | null; registry: Record<string, ChoiceFunction>; onNavigateToRegistry?: (entryId: string) => void }) {
  const { traceItem, registry, onNavigateToRegistry } = props;
  
  // Helper function to find choice function name by ID
  const findChoiceFunctionName = (funcId: string): string => {
    const entry = registry[funcId];
    if (entry) {
      return entry.interface.func;
    }
    // If not found, return the ID as fallback
    return funcId;
  };
  
  if (!traceItem) {
    return (
      <Box p={6} textAlign="center" color="gray.500">
        <Text>Select a function from the tree to view its details</Text>
      </Box>
    );
  }

  const entry = registry[traceItem.func];
  const impl = entry.funcs[traceItem.impl] || entry.interface; 
  
  return (
    <Box p={4}>
      <VStack align="start" gap={4}>
        {/* Function Header */}
        <Box>
          <HStack mb={2}>
            <Badge colorScheme="blue">Function</Badge>
            <Heading as="h3" size="md">{entry.interface.func}</Heading>
          </HStack>
        </Box>

        {/* TraceItem Fields */}
        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Function ID:</Text>
          <Code p={2} display="block" bg="gray.50" borderRadius="md" fontSize="xs">
            {traceItem.func}
          </Code>
        </Box>

        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Implementation:</Text>
          <Code p={2} display="block" bg="gray.50" borderRadius="md">
            {impl.func}
          </Code>
        </Box>

        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Implementation ID:</Text>
          <Code p={2} display="block" bg="gray.50" borderRadius="md" fontSize="xs">
            {traceItem.impl}
          </Code>
        </Box>

        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Arguments:</Text>
          <Code p={2} display="block" bg="gray.50" borderRadius="md">
            [{traceItem.args.join(', ')}]
          </Code>
        </Box>

        {traceItem.stack_info.length > 0 && (
          <Box w="100%">
            <Text fontWeight="semibold" mb={2}>Stack Info:</Text>
            <VStack align="start" gap={1}>
              {traceItem.stack_info.map((stackFrame, index) => (
                <Code key={index} p={1} display="block" bg="gray.50" borderRadius="sm" fontSize="xs" w="100%">
                  {stackFrame}
                </Code>
              ))}
            </VStack>
          </Box>
        )}

        {traceItem.rules.length > 0 && (
          <Box w="100%">
            <Text fontWeight="semibold" mb={2}>Matched Rules:</Text>
            <VStack align="start" gap={2}>
              {traceItem.rules.map((matchedRule, index) => (
                <Box key={index} p={2} bg="gray.50" borderRadius="md" w="100%">
                  <VStack align="start" gap={1}>
                    <HStack>
                      <Text fontSize="sm" fontWeight="medium">Selector:</Text>
                      <Code fontSize="sm">{matchedRule.rule.selector}</Code>
                    </HStack>
                    <HStack>
                      <Text fontSize="sm" fontWeight="medium">Impl:</Text>
                      <Code fontSize="sm">{findImplementationName(matchedRule.rule.impl, entry)}</Code>
                    </HStack>
                    <HStack>
                      <Text fontSize="sm" fontWeight="medium">Vals:</Text>
                      <Code fontSize="sm">{matchedRule.rule.vals}</Code>
                    </HStack>
                    {Object.keys(matchedRule.captures).length > 0 && (
                      <Box>
                        <Text fontSize="sm" fontWeight="medium">Captures:</Text>
                        <Code fontSize="xs" display="block" mt={1} whiteSpace="pre-wrap">
                          {JSON.stringify(matchedRule.captures, null, 2)}
                        </Code>
                      </Box>
                    )}
                  </VStack>
                </Box>
              ))}
            </VStack>
          </Box>
        )}

        {Object.keys(traceItem.kwargs).length > 0 && (
          <Box w="100%">
            <Text fontWeight="semibold" mb={2}>Kwargs:</Text>
            <Code p={2} display="block" bg="gray.50" borderRadius="md" whiteSpace="pre-wrap">
              {JSON.stringify(traceItem.kwargs, null, 2)}
            </Code>
          </Box>
        )}

        {Object.keys(traceItem.choice_kwargs).length > 0 && (
          <Box w="100%">
            <Text fontWeight="semibold" mb={2}>Choice Kwargs:</Text>
            <Code p={2} display="block" bg="gray.50" borderRadius="md" whiteSpace="pre-wrap">
              {JSON.stringify(traceItem.choice_kwargs, null, 2)}
            </Code>
          </Box>
        )}

        {traceItem.items.length > 0 && (
          <Box w="100%">
            <Text fontWeight="semibold" mb={2}>Nested Functions:</Text>
            <VStack align="start" gap={1}>
              {traceItem.items.map((nestedItem, index) => (
                <Badge key={index} colorScheme="green" size="sm">
                  {findChoiceFunctionName(nestedItem.func)}
                </Badge>
              ))}
            </VStack>
          </Box>
        )}

        {/* Registry Entry Fields */}
        <Box w="100%">
          <HStack mb={2} justify="space-between" align="center">
            <Text fontWeight="semibold">Registry Entry ID:</Text>
            {onNavigateToRegistry && (
              <Text
                fontSize="sm"
                color="blue.600"
                cursor="pointer"
                textDecoration="underline"
                _hover={{ color: "blue.800" }}
                onClick={() => onNavigateToRegistry(entry.id)}
              >
                View in Registry →
              </Text>
            )}
          </HStack>
          <Code p={2} display="block" bg="blue.50" borderRadius="md" fontSize="xs">
            {entry.id}
          </Code>
        </Box>

        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Interface Details:</Text>
          <Box p={2} bg="blue.50" borderRadius="md">
            <VStack align="start" gap={1}>
              <HStack>
                <Text fontSize="sm" fontWeight="medium">ID:</Text>
                <Code fontSize="xs">{entry.interface.id}</Code>
              </HStack>
              <HStack>
                <Text fontSize="sm" fontWeight="medium">Function:</Text>
                <Code fontSize="sm">{entry.interface.func}</Code>
              </HStack>
              {Object.keys(entry.interface.defaults).length > 0 && (
                <Box>
                  <Text fontSize="sm" fontWeight="medium">Defaults:</Text>
                  <Code fontSize="xs" display="block" mt={1} whiteSpace="pre-wrap">
                    {JSON.stringify(entry.interface.defaults, null, 2)}
                  </Code>
                </Box>
              )}
            </VStack>
          </Box>
        </Box>

        {Object.keys(entry.funcs).length > 0 && (
          <Box w="100%">
            <Text fontWeight="semibold" mb={2}>Available Functions:</Text>
            <VStack align="start" gap={2}>
              {Object.entries(entry.funcs).map(([funcName, funcImpl]) => (
                <Box key={funcName} p={2} bg="blue.50" borderRadius="md" w="100%">
                  <VStack align="start" gap={1}>
                    <HStack>
                      <Text fontSize="sm" fontWeight="medium">Name:</Text>
                      <Code fontSize="sm">{funcName}</Code>
                    </HStack>
                    <HStack>
                      <Text fontSize="sm" fontWeight="medium">ID:</Text>
                      <Code fontSize="xs">{funcImpl.id}</Code>
                    </HStack>
                    <HStack>
                      <Text fontSize="sm" fontWeight="medium">Function:</Text>
                      <Code fontSize="sm">{funcImpl.func}</Code>
                    </HStack>
                    {Object.keys(funcImpl.defaults).length > 0 && (
                      <Box>
                        <Text fontSize="sm" fontWeight="medium">Defaults:</Text>
                        <Code fontSize="xs" display="block" mt={1} whiteSpace="pre-wrap">
                          {JSON.stringify(funcImpl.defaults, null, 2)}
                        </Code>
                      </Box>
                    )}
                  </VStack>
                </Box>
              ))}
            </VStack>
          </Box>
        )}

        {entry.rules.length > 0 && (
          <Box w="100%">
            <Text fontWeight="semibold" mb={2}>Registry Rules:</Text>
            <VStack align="start" gap={2}>
              {entry.rules.map((rule, index) => (
                <Box key={index} p={2} bg="blue.50" borderRadius="md" w="100%">
                  <VStack align="start" gap={1}>
                    <HStack>
                      <Text fontSize="sm" fontWeight="medium">Selector:</Text>
                      <Code fontSize="sm">{rule.selector}</Code>
                    </HStack>
                    <HStack>
                      <Text fontSize="sm" fontWeight="medium">Impl:</Text>
                      <Code fontSize="sm">{findImplementationName(rule.impl, entry)}</Code>
                    </HStack>
                    <HStack>
                      <Text fontSize="sm" fontWeight="medium">Vals:</Text>
                      <Code fontSize="sm">{rule.vals}</Code>
                    </HStack>
                  </VStack>
                </Box>
              ))}
            </VStack>
          </Box>
        )}

        {/* Current Implementation Details */}
        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Current Implementation Details:</Text>
          <Box p={2} bg="green.50" borderRadius="md">
            <VStack align="start" gap={1}>
              <HStack>
                <Text fontSize="sm" fontWeight="medium">ID:</Text>
                <Code fontSize="xs">{impl.id}</Code>
              </HStack>
              <HStack>
                <Text fontSize="sm" fontWeight="medium">Function:</Text>
                <Code fontSize="sm">{impl.func}</Code>
              </HStack>
              {Object.keys(impl.defaults).length > 0 && (
                <Box>
                  <Text fontSize="sm" fontWeight="medium">Defaults:</Text>
                  <Code fontSize="xs" display="block" mt={1} whiteSpace="pre-wrap">
                    {JSON.stringify(impl.defaults, null, 2)}
                  </Code>
                </Box>
              )}
            </VStack>
          </Box>
        </Box>
      </VStack>
    </Box>
  );
}

function TraceItems(props: TraceItemsProps) {
    const { items, registry } = props;
    const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);

    // Helper function to find choice function name by ID
    const findChoiceFunctionName = (funcId: string): string => {
      const entry = registry[funcId];
      if (entry) {
        return entry.interface.func;
      }
      // If not found, return the ID as fallback
      return funcId;
    };

    const convertToTreeNodes = (traceItem: TraceItemData, currentDepth: number = 0, parentId: string = ''): TreeNode => {
      const nodeId = `${parentId}-${traceItem.func}-${currentDepth}`;
      return {
        id: nodeId,
        name: findChoiceFunctionName(traceItem.func),
        data: traceItem,
        children: traceItem.items.length > 0
          ? traceItem.items.map((child) => convertToTreeNodes(child, currentDepth + 1, nodeId))
          : undefined
      };
    };

    // Convert all trace items to tree nodes
    const allTreeNodes = items.map((item, index) => convertToTreeNodes(item, 0, `root-${index}`));

    const collection = createTreeCollection<TreeNode>({
      nodeToValue: (node) => node.id,
      nodeToString: (node) => node.name,
      rootNode: {
        id: "ROOT",
        name: "",
        data: items[0], // Use first item as fallback
        children: allTreeNodes,
      },
    });

    const handleSelectionChange = (node: any, event: any) => {
      event.stopPropagation();
      setSelectedNode(node);
    };

    return (
      <Grid templateColumns="1fr 2fr" gap={4} h="600px">
        <GridItem>
          <Box borderWidth="1px" borderRadius="md" h="100%" overflow="auto">
            <Box p={3} borderBottom="1px" borderColor="gray.200" bg="gray.50">
              <Text fontWeight="semibold" fontSize="sm">Function Tree</Text>
            </Box>
            <TreeView.Root collection={collection} >
              <TreeView.Tree p={2}>
                <TreeView.Node<TreeNode>
                  render={({ node, nodeState }) =>
                    nodeState.isBranch ? (
                      <TreeView.BranchControl>
                        <TreeView.BranchTrigger>
                         <TreeView.BranchIndicator asChild>
                            <LuChevronRight />
                          </TreeView.BranchIndicator>
                        </TreeView.BranchTrigger>
                        <Text
                          fontWeight="medium"
                          cursor="pointer"
                          _hover={{ color: "blue.600" }}
                          onClick={(e: any) => handleSelectionChange(node, e)}
                        >
                          {node.name}
                        </Text>
                        {node.children && node.children.length > 0 && (
                          <Badge colorScheme="gray" size="xs" ml={2}>
                            {node.children.length}
                          </Badge>
                        )}
                      </TreeView.BranchControl>
                    ) : (
                      <TreeView.Item>
                        <Text
                          cursor="pointer"
                          onClick={(e: any) => handleSelectionChange(node, e)}
                          _hover={{ color: "blue.600" }}
                        >
                          {node.name}
                        </Text>
                      </TreeView.Item>
                    )
                  }
                />
              </TreeView.Tree>
            </TreeView.Root>
          </Box>
        </GridItem>

        <GridItem>
          <Box borderWidth="1px" borderRadius="md" h="100%" overflow="auto">
            <Box p={3} borderBottom="1px" borderColor="gray.200" bg="gray.50">
              <Text fontWeight="semibold" fontSize="sm">Function Details</Text>
            </Box>
            <TraceDetails 
              traceItem={selectedNode ? selectedNode.data : null} 
              registry={props.registry} 
              onNavigateToRegistry={props.onNavigateToRegistry}
            />
          </Box>
        </GridItem>
      </Grid>
    );
}

export default TraceItems

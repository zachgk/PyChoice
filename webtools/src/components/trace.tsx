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
} from '@chakra-ui/react'
import { LuChevronRight } from "react-icons/lu"
import { useState } from 'react'
import type { TraceItemData, ChoiceFunction, MatchedRule } from './data';

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
  
  // Helper function to format function values by stripping newlines and truncating to at most 30 characters
  const formatFunctionValue = (value: string, maxLength: number = 30): string => {
    // Strip newline characters and replace with spaces
    const cleanedValue = value.replace(/\n/g, ' ');
    
    if (cleanedValue.length <= maxLength) {
      return cleanedValue;
    }
    return cleanedValue.substring(0, maxLength) + '...';
  };

  // Helper function to format function call
  const formatFunctionCall = (funcName: string, args: string[], kwargs: Record<string, string>): string => {
    let callStr = `${funcName}(`;
    
    // Add positional arguments with formatting
    const argParts = [];
    if (args.length > 0) {
      argParts.push(...args.map(arg => formatFunctionValue(arg)));
    }
    
    // Add keyword arguments with formatting
    const kwargEntries = Object.entries(kwargs);
    if (kwargEntries.length > 0) {
      argParts.push(...kwargEntries.map(([key, value]) => `${key}=${formatFunctionValue(value)}`));
    }
    
    // Join arguments with proper formatting
    if (argParts.length > 0) {
      if (argParts.length === 1) {
        callStr += argParts[0];
      } else {
        callStr += '\n  ' + argParts.join(',\n  ') + '\n';
      }
    }
    
    callStr += ')';
    return callStr;
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
  
  const defRule: MatchedRule = {
    rule: {selector: '<defaults>', impl: impl.func, vals: ''},
    captures: {}};
  const allRules = [defRule, ...traceItem.rules];
  return (
    <Box p={4}>
      <VStack align="start" gap={4}>
        {/* Base Call */}
        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Base Call:</Text>
          <Code p={3} display="block" bg="gray.100" borderRadius="md" fontSize="sm" whiteSpace="pre-wrap">
            {formatFunctionCall(entry.interface.func, traceItem.args, traceItem.kwargs)}
          </Code>
        </Box>

        {/* Computed Choice Call */}
        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Computed Choice Call:</Text>
          <Code p={3} display="block" bg="green.100" borderRadius="md" fontSize="sm" whiteSpace="pre-wrap">
            {formatFunctionCall(impl.func, traceItem.args, traceItem.choice_kwargs)}
          </Code>
        </Box>

        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Matched Rules:</Text>
          <VStack align="start" gap={2}>
            {allRules.reverse().map((matchedRule, index) => (
              <Box key={index} p={2} bg="gray.50" borderRadius="md" w="100%">
                <VStack align="start" gap={1}>
                  <HStack>
                    <Text fontSize="sm" fontWeight="medium">Selector:</Text>
                    <Code fontSize="sm">{matchedRule.rule.selector}</Code>
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

        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Call Stack:</Text>
          <VStack align="start" gap={1}>
            {traceItem.stack_info.map((stackFrame, index) => (
              <Code key={index} p={1} display="block" bg="gray.50" borderRadius="sm" fontSize="xs" w="100%">
                {stackFrame}
              </Code>
            ))}
          </VStack>
        </Box>

        <Box w="100%">
          <HStack mb={2} justify="space-between" align="center">
            <Text fontWeight="semibold">Choice Function</Text>
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
            {entry.interface.func}
          </Code>
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

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
import type { TraceItemData } from './data';

interface TraceItemsProps {
    items: TraceItemData[];
}

interface TreeNode {
  id: string;
  name: string;
  data: TraceItemData;
  children?: TreeNode[];
}

function TraceDetails(props: { traceItem: TraceItemData | null }) {
  const { traceItem } = props;
  if (!traceItem) {
    return (
      <Box p={6} textAlign="center" color="gray.500">
        <Text>Select a function from the tree to view its details</Text>
      </Box>
    );
  }

  return (
    <Box p={4}>
      <VStack align="start" gap={4}>
        <Box>
          <HStack mb={2}>
            <Badge colorScheme="blue">Function</Badge>
            <Heading as="h3" size="md">{traceItem.func}</Heading>
          </HStack>
        </Box>

        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Implementation:</Text>
          <Code p={2} display="block" bg="gray.50" borderRadius="md">
            {traceItem.impl}
          </Code>
        </Box>
        
        <Box w="100%">
          <Text fontWeight="semibold" mb={2}>Arguments:</Text>
          <Code p={2} display="block" bg="gray.50" borderRadius="md">
            [{traceItem.args.join(', ')}]
          </Code>
        </Box>
        
        {traceItem.rules.length > 0 && (
          <Box w="100%">
            <Text fontWeight="semibold" mb={2}>Rules:</Text>
            <Code p={2} display="block" bg="gray.50" borderRadius="md" whiteSpace="pre-wrap">
              {JSON.stringify(traceItem.rules, null, 2)}
            </Code>
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
                  {nestedItem.func}
                </Badge>
              ))}
            </VStack>
          </Box>
        )}
      </VStack>
    </Box>
  );
}

function TraceItems(props: TraceItemsProps) {
    const { items } = props;
    const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);
    
    const convertToTreeNodes = (traceItem: TraceItemData, currentDepth: number = 0, parentId: string = ''): TreeNode => {
      const nodeId = `${parentId}-${traceItem.func}-${currentDepth}`;
      return {
        id: nodeId,
        name: traceItem.func,
        data: traceItem,
        children: traceItem.items.length > 0 
          ? traceItem.items.map((child, index) => convertToTreeNodes(child, currentDepth + 1, nodeId))
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
            <TraceDetails traceItem={selectedNode ? selectedNode.data : null} />
          </Box>
        </GridItem>
      </Grid>
    );
}  

export default TraceItems
